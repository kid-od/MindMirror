"""Milvus 客户端 - 支持密集向量+稀疏向量混合检索"""
import os
import time
from dotenv import load_dotenv
from pymilvus import MilvusClient, DataType, AnnSearchRequest, RRFRanker
from pymilvus.exceptions import MilvusException

load_dotenv()

# Milvus 单次 query 的 limit 上限（超出会报 invalid max query result window）
QUERY_MAX_LIMIT = 16384
DEFAULT_CONSISTENCY_LEVEL = "Strong"
DEFAULT_CLIENT_MAX_IDLE_SECONDS = float(os.getenv("MILVUS_CLIENT_MAX_IDLE_SECONDS", "300"))


class MilvusManager:
    """Milvus 连接和集合管理 - 支持混合检索"""

    def __init__(self, collection_name: str | None = None):
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = os.getenv("MILVUS_PORT", "19530")
        self.collection_name = collection_name or os.getenv("MILVUS_COLLECTION", "embeddings_collection")
        self.uri = f"http://{self.host}:{self.port}"
        self.client = None
        self.client_last_used_at: float | None = None
        self.client_max_idle_seconds = DEFAULT_CLIENT_MAX_IDLE_SECONDS

    def _close_client(self, client: MilvusClient | None) -> None:
        if client is None:
            return
        close = getattr(client, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    def _client_is_idle(self) -> bool:
        if self.client is None or self.client_last_used_at is None:
            return False
        if self.client_max_idle_seconds <= 0:
            return False
        return (time.monotonic() - self.client_last_used_at) >= self.client_max_idle_seconds

    def _get_client(self) -> MilvusClient:
        # Lazy-create client to avoid blocking app import/startup when Milvus is temporarily unavailable.
        if self._client_is_idle():
            self._reset_client()
        if self.client is None:
            self.client = MilvusClient(uri=self.uri)
        return self.client

    def _mark_client_used(self) -> None:
        self.client_last_used_at = time.monotonic()

    def _reset_client(self) -> None:
        stale_client = self.client
        self.client = None
        self.client_last_used_at = None
        self._close_client(stale_client)

    @staticmethod
    def _is_stale_connection_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return (
            "closed channel" in message
            or "channel closed" in message
            or "failed to connect" in message
        )

    def _call_with_reconnect(self, operation):
        client = self._get_client()
        try:
            result = operation(client)
            self._mark_client_used()
            return result
        except Exception as exc:
            if not self._is_stale_connection_error(exc):
                raise
            self._reset_client()
            client = self._get_client()
            result = operation(client)
            self._mark_client_used()
            return result

    def _flush_collection(self) -> None:
        def operation(client):
            flush = getattr(client, "flush", None)
            if callable(flush):
                flush(collection_name=self.collection_name)

        self._call_with_reconnect(operation)

    def init_collection(self, dense_dim: int | None = None):
        """
        初始化 Milvus 集合 - 同时支持密集向量和稀疏向量
        :param dense_dim: 密集向量维度；默认读环境变量 DENSE_EMBEDDING_DIM（本地 BAAI/bge-m3 为 1024）
        """
        if dense_dim is None:
            dense_dim = int(os.getenv("DENSE_EMBEDDING_DIM", "1024"))
        def operation(client):
            if not client.has_collection(self.collection_name):
                schema = client.create_schema(auto_id=True, enable_dynamic_field=True)
                
                # 主键
                schema.add_field("id", DataType.INT64, is_primary=True, auto_id=True)
                
                # 密集向量（来自 embedding 模型）
                schema.add_field("dense_embedding", DataType.FLOAT_VECTOR, dim=dense_dim)
                
                # 稀疏向量（来自 BM25）
                schema.add_field("sparse_embedding", DataType.SPARSE_FLOAT_VECTOR)
                
                # 文本和元数据字段
                schema.add_field("text", DataType.VARCHAR, max_length=2000)
                schema.add_field("filename", DataType.VARCHAR, max_length=255)
                schema.add_field("file_type", DataType.VARCHAR, max_length=50)
                schema.add_field("file_path", DataType.VARCHAR, max_length=1024)
                schema.add_field("page_number", DataType.INT64)
                schema.add_field("chunk_idx", DataType.INT64)

                # Auto-merging 所需层级字段
                schema.add_field("chunk_id", DataType.VARCHAR, max_length=512)
                schema.add_field("parent_chunk_id", DataType.VARCHAR, max_length=512)
                schema.add_field("root_chunk_id", DataType.VARCHAR, max_length=512)
                schema.add_field("chunk_level", DataType.INT64)
                schema.add_field("visibility", DataType.VARCHAR, max_length=20)
                schema.add_field("owner_id", DataType.VARCHAR, max_length=100)
                schema.add_field("document_domain", DataType.VARCHAR, max_length=50)

                # 为两种向量分别创建索引
                index_params = client.prepare_index_params()
                
                # 密集向量索引 - 使用 HNSW（更适合混合检索）
                index_params.add_index(
                    field_name="dense_embedding",
                    index_type="HNSW",
                    metric_type="IP",
                    params={"M": 16, "efConstruction": 256}
                )
                
                # 稀疏向量索引
                index_params.add_index(
                    field_name="sparse_embedding",
                    index_type="SPARSE_INVERTED_INDEX",
                    metric_type="IP",
                    params={"drop_ratio_build": 0.2}
                )

                client.create_collection(
                    collection_name=self.collection_name,
                    schema=schema,
                    index_params=index_params,
                    consistency_level=DEFAULT_CONSISTENCY_LEVEL,
                )

        self._call_with_reconnect(operation)

    def insert(self, data: list[dict]):
        """插入数据到 Milvus"""
        result = self._call_with_reconnect(lambda client: client.insert(self.collection_name, data))
        self._flush_collection()
        return result

    def query(
        self,
        filter_expr: str = "",
        output_fields: list[str] = None,
        limit: int = 10000,
        offset: int = 0,
    ):
        """查询数据。limit 不宜超过 QUERY_MAX_LIMIT。"""
        return self._call_with_reconnect(lambda client: client.query(
            collection_name=self.collection_name,
            filter=filter_expr,
            output_fields=output_fields or ["filename", "file_type"],
            limit=min(limit, QUERY_MAX_LIMIT),
            offset=offset,
            consistency_level=DEFAULT_CONSISTENCY_LEVEL,
        ))

    def query_all(self, filter_expr: str = "", output_fields: list[str] | None = None) -> list:
        """分页拉取匹配 filter 的全部行，避免单次 limit 超过服务端窗口。"""
        fields = output_fields or ["filename", "file_type"]
        out: list = []
        offset = 0
        while True:
            batch = self._call_with_reconnect(lambda client: client.query(
                collection_name=self.collection_name,
                filter=filter_expr,
                output_fields=fields,
                limit=QUERY_MAX_LIMIT,
                offset=offset,
                consistency_level=DEFAULT_CONSISTENCY_LEVEL,
            ))
            if not batch:
                break
            out.extend(batch)
            if len(batch) < QUERY_MAX_LIMIT:
                break
            offset += len(batch)
        return out

    def get_chunks_by_ids(self, chunk_ids: list[str]) -> list[dict]:
        """根据 chunk_id 批量查询分块（用于 Auto-merging 拉取父块）"""
        ids = [item for item in chunk_ids if item]
        if not ids:
            return []
        quoted_ids = ", ".join([f'"{item}"' for item in ids])
        filter_expr = f"chunk_id in [{quoted_ids}]"
        return self.query(
            filter_expr=filter_expr,
            output_fields=[
                "text",
                "filename",
                "file_type",
                "page_number",
                "chunk_id",
                "parent_chunk_id",
                "root_chunk_id",
                "chunk_level",
                "chunk_idx",
                "visibility",
                "owner_id",
                "document_domain",
            ],
            limit=len(ids),
        )

    def hybrid_retrieve(
        self,
        dense_embedding: list[float],
        sparse_embedding: dict,
        top_k: int = 5,
        rrf_k: int = 60,     #可调节
        filter_expr: str = "",
    ) -> list[dict]:
        """
        混合检索 - 使用 RRF 融合密集向量和稀疏向量的检索结果
        
        :param dense_embedding: 密集向量
        :param sparse_embedding: 稀疏向量 {index: value, ...}
        :param top_k: 返回结果数量
        :param rrf_k: RRF 算法参数 k，默认60
        :return: 检索结果列表
        """
        output_fields = [
            "text",
            "filename",
            "file_type",
            "page_number",
            "chunk_id",
            "parent_chunk_id",
            "root_chunk_id",
            "chunk_level",
            "chunk_idx",
            "visibility",
            "owner_id",
            "document_domain",
        ]
        
        # 密集向量搜索请求
        dense_search = AnnSearchRequest(
            data=[dense_embedding],
            anns_field="dense_embedding",
            param={"metric_type": "IP", "params": {"ef": 64}},
            limit=top_k * 2,  # 多取一些用于融合
            expr=filter_expr,
        )
        
        # 稀疏向量搜索请求
        sparse_search = AnnSearchRequest(
            data=[sparse_embedding],
            anns_field="sparse_embedding",
            param={"metric_type": "IP", "params": {"drop_ratio_search": 0.2}},
            limit=top_k * 2,
            expr=filter_expr,
        )
        
        # 使用 RRF 排序算法融合结果
        reranker = RRFRanker(k=rrf_k)
        
        results = self._call_with_reconnect(lambda client: client.hybrid_search(
            collection_name=self.collection_name,
            reqs=[dense_search, sparse_search],
            ranker=reranker,
            limit=top_k,
            output_fields=output_fields,
            consistency_level=DEFAULT_CONSISTENCY_LEVEL,
        ))
        
        # 格式化返回结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.get("id"),
                    "text": hit.get("text", ""),
                    "filename": hit.get("filename", ""),
                    "file_type": hit.get("file_type", ""),
                    "page_number": hit.get("page_number", 0),
                    "chunk_id": hit.get("chunk_id", ""),
                    "parent_chunk_id": hit.get("parent_chunk_id", ""),
                    "root_chunk_id": hit.get("root_chunk_id", ""),
                    "chunk_level": hit.get("chunk_level", 0),
                    "chunk_idx": hit.get("chunk_idx", 0),
                    "visibility": hit.get("visibility", ""),
                    "owner_id": hit.get("owner_id", ""),
                    "document_domain": hit.get("document_domain", ""),
                    "score": hit.get("distance", 0.0)
                })
        
        return formatted_results

    def dense_retrieve(self, dense_embedding: list[float], top_k: int = 5, filter_expr: str = "") -> list[dict]:
        """
        仅使用密集向量检索（降级模式，用于稀疏向量不可用时）
        """
        results = self._call_with_reconnect(lambda client: client.search(
            collection_name=self.collection_name,
            data=[dense_embedding],
            anns_field="dense_embedding",
            search_params={"metric_type": "IP", "params": {"ef": 64}},
            limit=top_k,
            output_fields=[
                "text",
                "filename",
                "file_type",
                "page_number",
                "chunk_id",
                "parent_chunk_id",
                "root_chunk_id",
                "chunk_level",
                "chunk_idx",
                "visibility",
                "owner_id",
                "document_domain",
            ],
            filter=filter_expr,
            consistency_level=DEFAULT_CONSISTENCY_LEVEL,
        ))
        
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.get("id"),
                    "text": hit.get("entity", {}).get("text", ""),
                    "filename": hit.get("entity", {}).get("filename", ""),
                    "file_type": hit.get("entity", {}).get("file_type", ""),
                    "page_number": hit.get("entity", {}).get("page_number", 0),
                    "chunk_id": hit.get("entity", {}).get("chunk_id", ""),
                    "parent_chunk_id": hit.get("entity", {}).get("parent_chunk_id", ""),
                    "root_chunk_id": hit.get("entity", {}).get("root_chunk_id", ""),
                    "chunk_level": hit.get("entity", {}).get("chunk_level", 0),
                    "chunk_idx": hit.get("entity", {}).get("chunk_idx", 0),
                    "visibility": hit.get("entity", {}).get("visibility", ""),
                    "owner_id": hit.get("entity", {}).get("owner_id", ""),
                    "document_domain": hit.get("entity", {}).get("document_domain", ""),
                    "score": hit.get("distance", 0.0)
                })
        
        return formatted_results

    def delete(self, filter_expr: str):
        """删除数据"""
        result = self._call_with_reconnect(lambda client: client.delete(
            collection_name=self.collection_name,
            filter=filter_expr
        ))
        self._flush_collection()
        return result

    def has_collection(self) -> bool:
        """检查集合是否存在"""
        return self._call_with_reconnect(lambda client: client.has_collection(self.collection_name))

    def drop_collection(self):
        """删除集合（用于重建 schema）"""
        def operation(client):
            if client.has_collection(self.collection_name):
                client.drop_collection(self.collection_name)

        self._call_with_reconnect(operation)
