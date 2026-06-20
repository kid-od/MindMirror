"""活动聚合路由：每日一句、洞察面板和时间线。"""

try:
    import api_context as ctx
except ModuleNotFoundError:
    from backend import api_context as ctx


router = ctx.APIRouter()


@router.get("/daily-quote", response_model=ctx.DailyQuoteResponse)
async def daily_quote(
    locale: str = ctx.Query(default="zh", pattern="^(zh|en)$"),
    _: ctx.User = ctx.Depends(ctx.get_current_user),
):
    try:
        return ctx.DailyQuoteResponse(**ctx.get_daily_quote(locale))
    except Exception as e:
        raise ctx.HTTPException(status_code=500, detail=f"获取每日一句失败: {str(e)}")


@router.get("/insights", response_model=ctx.InsightsResponse)
async def get_insights(current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    essays = ctx.essay_store.list_by_owner(current_user.username)
    sessions = ctx.storage.list_session_infos(current_user.username)
    documents = ctx.list_public_document_activity() if current_user.role == "admin" else []
    return ctx.InsightsResponse(**ctx.build_insights_payload(essays, sessions, documents))


@router.get("/timeline", response_model=ctx.TimelineResponse)
async def get_timeline(current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    essays = ctx.essay_store.list_by_owner(current_user.username)
    sessions = ctx.storage.list_session_infos(current_user.username)
    documents = ctx.list_public_document_activity() if current_user.role == "admin" else []
    return ctx.TimelineResponse(**ctx.build_timeline_payload(essays, sessions, documents))
