const { createApp } = Vue;

const TOP_THEMES = {
    zh: ['存在主义', '斯多葛主义', '荒诞', '决定论', '伦理'],
    en: ['Existentialism', 'Stoicism', 'Absurdity', 'Determinism', 'Ethics']
};

const CHAT_SUGGESTIONS = {
    zh: [
        '追溯我总是匆忙的根源。',
        '看看孤立状态带给我的隐性收益。',
        '梳理我的价值观和日程安排之间的张力。'
    ],
    en: [
        'Trace the origin of the rushing habit.',
        'Examine the secondary gains of isolation.',
        'Map the tension between my values and my schedule.'
    ]
};

const DEFAULT_DAILY_QUOTES = {
    zh: {
        text: '允许自己慢一点，也是在认真地活着。',
        author: 'PsycheArchive',
        language: 'zh',
        source: 'local',
        fallback: true
    },
    en: {
        text: 'You are allowed to move slowly and still be growing.',
        author: 'PsycheArchive',
        language: 'en',
        source: 'local',
        fallback: true
    }
};

const VIEW_ALIASES = {
    knowledge: 'knowledge_base',
    essays: 'reflections',
    chat: 'ai_explorer'
};

const TRANSLATIONS = {
    zh: {
        app: {
            name: 'PsycheArchive',
            subtitle: '心灵策展人',
            authCopy: '一个面向心理学、哲学与自我剖析的沉浸式 RAG 工作台。',
            localeToggle: '中文 / EN',
            themeLight: '浅色',
            themeDark: '深色'
        },
        auth: {
            username: '用户名',
            password: '密码',
            adminInvite: '管理员邀请码',
            login: '登录',
            register: '注册',
            loginSubmitting: '提交中...',
            toRegister: '没有账号？创建账号',
            toLogin: '已有账号？返回登录',
            roleUser: '普通用户',
            roleAdmin: '管理员'
        },
        nav: {
            dashboard: '仪表盘',
            knowledge_base: '知识库',
            reflections: '随笔档案',
            ai_explorer: 'AI 探索',
            insights: '洞察',
            timeline: '时间线',
            knowledge: '知识库',
            essays: '我的随笔',
            chat: 'AI 对话',
            settings: '设置'
        },
        profile: {
            admin: '管理员策展人',
            user: '自我探索用户',
            logout: '退出登录'
        },
        dashboard: {
            quoteLoading: '正在获取今日治愈语句...',
            totalEssays: '累计写下的随笔',
            topThemes: '高频主题',
            knowledgeCoverage: '知识库覆盖率',
            publicDocs: '公开资料',
            privateEssays: '私密随笔',
            deepSessions: '深度会话',
            startSession: '开始会话',
            recentEssays: '最近随笔',
            viewAll: '查看全部',
            emptyEssays: '上传一篇反思、随笔或 Markdown 日志，开始建立你的私人档案。',
            lastAnalysis: '最近分析主题',
            openChat: '打开对话',
            knowledgeActive: '知识库已启用',
            updatedMessages: '更新于 {date} · {count} 条消息',
            ready: 'The Mindful Curator 已准备好，随时陪你进入更深的反思。'
        },
        knowledge: {
            title: '知识库',
            restricted: '此区域仅对管理员开放。',
            hero: '策展心理学、哲学与其他基础文本，作为认知引擎的公共知识来源。支持上传 PDF、DOCX 或 MD 文件。',
            newUpload: '新建上传',
            dropTitle: '拖拽文档到这里',
            dropBody: '支持格式：PDF、DOCX、MD（单文件最大 50MB）',
            browse: '或浏览文件',
            loading: '正在加载知识库...',
            empty: '暂时还没有公开资料被索引。',
            sourceCaption: '这是面向所有反思会话开放的公共知识来源。',
            delete: '删除'
        },
        essays: {
            title: '你的数字花园',
            hero: '培育你的想法，识别反复出现的主题，并请求 AI 对过往文字做分步式心理反思。',
            newEntry: '新建日记',
            loading: '正在加载你的反思',
            loadingBody: '花园正在准备中。',
            empty: '还没有日记条目',
            emptyBody: '上传一篇反思、随笔或 Markdown 日志，开始建立你的私人档案。',
            analyzed: '已分析',
            chunkLabel: '个私密反思分块，已用于自我分析',
            delete: '删除',
            viewInsights: '查看洞察'
        },
        chat: {
            recents: '最近对话',
            quickPrompts: '快速引导',
            new: '新建',
            emptySessions: '第一次对话之后，这里会显示你的历史会话。',
            sessionTitleFallback: '新对话',
            deleteSession: '删除会话',
            deleteConfirm: '确定要删除这个会话吗？',
            deleteFailed: '删除会话失败：{message}',
            title: '深度分析会话',
            subtitle: '一起梳理你近期文字背后的模式、张力与价值感。',
            knowledgeActive: '知识库已启用',
            welcomeTitle: 'The Mindful Curator 已准备就绪。',
            welcomeBody: '分享你想要一起审视的一段反思、一个反复出现的习惯，或者一种难以命名的情绪。',
            thinking: 'The curator 正在思考...',
            references: '参考资料：{filename}',
            options: '分步分析选项：',
            optionOrigin: '追溯根源',
            optionGains: '看看隐性收益',
            noExcerpt: '暂无摘录内容。',
            processingFailed: '这次反思没有顺利完成，请稍后再试。',
            inputPlaceholder: '写下你的反思...',
            disclaimer: 'AI 反思用于自我探索，不构成临床建议。',
            stop: '停止',
            unavailable: 'The Mindful Curator 暂时不可用：{message}',
            aborted: '（已终止回答）'
        },
        settings: {
            title: '设置',
            subtitle: '查看你的反思工作台与账号状态。',
            admin: '管理员策展人',
            user: '自我探索用户',
            signedIn: '已登录，随时可以开始自我分析会话。',
            totals: '工作台统计',
            publicDocs: '份公开资料',
            privateEssays: '篇私密随笔',
            pastReflections: '个历史反思会话'
        },
        common: {
            justNow: '刚刚',
            loading: '加载中...',
            uploadFailed: '上传失败：{message}',
            unknownError: '未知错误',
            loginRequired: '请先登录',
            authExpired: '登录已过期，请重新登录',
            authFailed: '认证失败',
            usernamePasswordRequired: '用户名和密码不能为空',
            uploadChooseFile: '请先选择文件',
            browserStreamUnsupported: '浏览器不支持流式响应',
            browserUploadStreamUnsupported: '浏览器不支持流式上传响应',
            searchKnowledge: '搜索知识库...',
            searchEssays: '搜索随笔...',
            searchInsights: '搜索洞察...',
            searchReflections: '搜索你的反思...',
            untitledReflection: '未命名反思',
            reflectionSession: '反思会话',
            deleteDocumentConfirm: '确定要删除文档 “{filename}” 吗？',
            deleteEssayConfirm: '确定要删除随笔 “{filename}” 吗？',
            deleteDocumentFailed: '删除知识库文档失败：{message}',
            deleteEssayFailed: '删除随笔失败：{message}',
            loadSessionsFailed: '加载历史记录失败：{message}',
            loadSessionFailed: '加载会话失败：{message}',
            loadKnowledgeFailed: '加载知识库失败：{message}',
            loadEssaysFailed: '加载随笔失败：{message}',
            loadSessionsFallback: '无法加载历史记录',
            loadSessionFallback: '无法加载会话内容',
            loadKnowledgeFallback: '无法加载知识库',
            loadEssaysFallback: '无法加载随笔',
            preparingUpload: '准备上传 {count} 个文件...',
            fileUploaded: '{filename} 上传完成',
            partialUploadFailed: '已有 {count} 个文件上传失败，继续处理剩余文件...',
            uploadComplete: '上传完成',
            uploadMissingResult: '上传流程未返回完成结果',
            askAnalyzeEssay: '请帮我一步步分析这篇反思《{title}》。'
        }
    },
    en: {
        app: {
            name: 'PsycheArchive',
            subtitle: 'The Mindful Curator',
            authCopy: 'An immersive RAG workspace for psychology, philosophy, and self-analysis.',
            localeToggle: '中文 / EN',
            themeLight: 'Light',
            themeDark: 'Dark'
        },
        auth: {
            username: 'Username',
            password: 'Password',
            adminInvite: 'Admin Invite Code',
            login: 'Login',
            register: 'Register',
            loginSubmitting: 'Submitting...',
            toRegister: 'No account? Create one',
            toLogin: 'Already have an account? Back to login',
            roleUser: 'User',
            roleAdmin: 'Admin'
        },
        nav: {
            dashboard: 'Dashboard',
            knowledge_base: 'Knowledge Base',
            reflections: 'Reflections',
            ai_explorer: 'AI Explorer',
            insights: 'Insights',
            timeline: 'Timeline',
            knowledge: 'Knowledge Base',
            essays: 'My Essays',
            chat: 'AI Chat',
            settings: 'Settings'
        },
        profile: {
            admin: 'Admin Curator',
            user: 'Reflective User',
            logout: 'Log Out'
        },
        dashboard: {
            quoteLoading: 'Fetching today’s healing words...',
            totalEssays: 'Total Essays Written',
            topThemes: 'Top Themes',
            knowledgeCoverage: 'Knowledge Base Coverage',
            publicDocs: 'public docs',
            privateEssays: 'private essays',
            deepSessions: 'Deep Sessions',
            startSession: 'Start Session',
            recentEssays: 'Recent Essays',
            viewAll: 'View All',
            emptyEssays: 'Upload a reflection, essay, or markdown journal to start your private archive.',
            lastAnalysis: 'Last Analysis Topic',
            openChat: 'Open Chat',
            knowledgeActive: 'Knowledge Base Active',
            updatedMessages: 'Updated {date} · {count} messages',
            ready: 'The Mindful Curator is ready whenever you want to begin a deeper reflection.'
        },
        knowledge: {
            title: 'Knowledge Base',
            restricted: 'This area is reserved for admin curators.',
            hero: 'Curate psychology, philosophy, and foundational texts for the cognitive engine. Upload PDF, DOCX, or MD files.',
            newUpload: 'New Upload',
            dropTitle: 'Drag & Drop Documents',
            dropBody: 'Supported formats: PDF, DOCX, MD (Max 50MB per file)',
            browse: 'or browse files',
            loading: 'Loading knowledge base...',
            empty: 'No public documents indexed yet.',
            sourceCaption: 'Public knowledge source available to every reflective session.',
            delete: 'Delete'
        },
        essays: {
            title: 'Your Digital Garden',
            hero: 'Cultivate your thoughts, track recurring themes, and request AI-guided psychological reflection on your past entries.',
            newEntry: 'New Journal Entry',
            loading: 'Loading your reflections',
            loadingBody: 'The garden is being prepared.',
            empty: 'No journal entries yet',
            emptyBody: 'Upload a reflection, essay, or markdown journal to start your private archive.',
            analyzed: 'Analyzed',
            chunkLabel: 'private reflection chunks indexed for self-analysis',
            delete: 'Delete',
            viewInsights: 'View Insights'
        },
        chat: {
            recents: 'Recents',
            quickPrompts: 'Quick Prompts',
            new: 'New',
            emptySessions: 'Your past conversations will appear here after your first chat.',
            sessionTitleFallback: 'New Chat',
            deleteSession: 'Delete session',
            deleteConfirm: 'Delete this session?',
            deleteFailed: 'Failed to delete session: {message}',
            title: 'Deep Analysis Session',
            subtitle: 'Reflecting on the patterns, tensions, and values behind your recent writing.',
            knowledgeActive: 'Knowledge Base Active',
            welcomeTitle: 'The Mindful Curator is ready.',
            welcomeBody: 'Share a reflection, tension, or recurring pattern you want to examine.',
            thinking: 'The curator is reflecting...',
            references: 'Reference: {filename}',
            options: 'Step-by-step analysis options:',
            optionOrigin: 'Trace the origin',
            optionGains: 'Examine secondary gains',
            noExcerpt: 'No excerpt available.',
            processingFailed: 'The curator could not complete this reflection.',
            inputPlaceholder: 'Share your reflections...',
            disclaimer: 'AI reflections are for self-exploration, not clinical advice.',
            stop: 'Stop',
            unavailable: 'The Mindful Curator is temporarily unavailable: {message}',
            aborted: '(Response stopped)'
        },
        settings: {
            title: 'Settings',
            subtitle: 'Keep track of your reflective workspace and account status.',
            admin: 'Admin Curator',
            user: 'Reflective User',
            signedIn: 'Signed in and ready for self-analysis sessions.',
            totals: 'Workspace Totals',
            publicDocs: 'public documents',
            privateEssays: 'private essays',
            pastReflections: 'past reflections'
        },
        common: {
            justNow: 'Just now',
            loading: 'Loading...',
            uploadFailed: 'Upload failed: {message}',
            unknownError: 'Unknown error',
            loginRequired: 'Please log in first',
            authExpired: 'Your session expired. Please log in again.',
            authFailed: 'Authentication failed',
            usernamePasswordRequired: 'Username and password are required',
            uploadChooseFile: 'Please choose at least one file',
            browserStreamUnsupported: 'Your browser does not support streaming responses',
            browserUploadStreamUnsupported: 'Your browser does not support streaming upload responses',
            searchKnowledge: 'Search knowledge base...',
            searchEssays: 'Search essays...',
            searchInsights: 'Search insights...',
            searchReflections: 'Search your reflections...',
            untitledReflection: 'Untitled Reflection',
            reflectionSession: 'Reflection Session',
            deleteDocumentConfirm: 'Delete document "{filename}"?',
            deleteEssayConfirm: 'Delete essay "{filename}"?',
            deleteDocumentFailed: 'Failed to delete knowledge document: {message}',
            deleteEssayFailed: 'Failed to delete essay: {message}',
            loadSessionsFailed: 'Failed to load session history: {message}',
            loadSessionFailed: 'Failed to load session: {message}',
            loadKnowledgeFailed: 'Failed to load knowledge base: {message}',
            loadEssaysFailed: 'Failed to load essays: {message}',
            loadSessionsFallback: 'Unable to load session history',
            loadSessionFallback: 'Unable to load session messages',
            loadKnowledgeFallback: 'Unable to load knowledge base',
            loadEssaysFallback: 'Unable to load essays',
            preparingUpload: 'Preparing to upload {count} files...',
            fileUploaded: '{filename} uploaded',
            partialUploadFailed: '{count} files failed, continuing with the rest...',
            uploadComplete: 'Upload complete',
            uploadMissingResult: 'The upload stream did not return a completion event',
            askAnalyzeEssay: 'Please help me analyze the reflection "{title}" step by step.'
        }
    }
};

function currentLocale() {
    return localStorage.getItem('locale') === 'en' ? 'en' : 'zh';
}

function localizedCommonText(key, fallback) {
    const locale = currentLocale();
    return (TRANSLATIONS[locale] && TRANSLATIONS[locale].common && TRANSLATIONS[locale].common[key]) || fallback;
}

function essayTitle(filename) {
    return (filename || localizedCommonText('untitledReflection', 'Untitled Reflection'))
        .replace(/\.[^.]+$/, '')
        .replace(/[_-]+/g, ' ')
        .trim();
}

function sessionLabel(sessionId) {
    const locale = currentLocale();
    if (!sessionId) return localizedCommonText('reflectionSession', 'Reflection Session');
    if (/^session_\d+$/.test(sessionId)) {
        const timestamp = Number(sessionId.replace('session_', ''));
        if (!Number.isNaN(timestamp)) {
            return new Date(timestamp).toLocaleString(locale === 'zh' ? 'zh-CN' : 'en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
    return sessionId;
}

function defaultDailyQuote(locale) {
    return { ...(locale === 'zh' ? DEFAULT_DAILY_QUOTES.zh : DEFAULT_DAILY_QUOTES.en) };
}

function emptyInsights() {
    return {
        totals: { essays: 0, sessions: 0, documents: 0 },
        top_themes: [],
        activity: [],
        recent_essays: [],
        recent_sessions: []
    };
}

function normalizeDailyQuote(quote, locale = 'zh') {
    const fallback = defaultDailyQuote(locale);
    const candidate = quote && typeof quote === 'object' ? quote : {};
    const text = typeof candidate.text === 'string' ? candidate.text.trim() : '';
    const author = typeof candidate.author === 'string' ? candidate.author.trim() : '';
    const source = typeof candidate.source === 'string' ? candidate.source.trim() : '';
    const language = candidate.language === 'zh' ? 'zh' : candidate.language === 'en' ? 'en' : fallback.language;

    if (!text) {
        return fallback;
    }

    return {
        text,
        author: author || fallback.author,
        language,
        source: source || fallback.source,
        fallback: Boolean(candidate.fallback)
    };
}

createApp({
    data() {
        return {
            messages: [],
            userInput: '',
            isLoading: false,
            abortController: null,
            sessionId: `session_${Date.now()}`,
            activeEssayId: '',
            activeEssayTitle: '',
            analysisMode: 'general',
            sessions: [],
            insights: emptyInsights(),
            insightsLoading: false,
            timelineGroups: [],
            timelineLoading: false,
            dailyQuote: normalizeDailyQuote(null, localStorage.getItem('locale') || 'zh'),
            dailyQuoteLoading: false,
            isComposing: false,
            currentView: 'dashboard',
            globalSearch: '',
            documents: [],
            documentsLoading: false,
            essays: [],
            essaysLoading: false,
            selectedKnowledgeFiles: [],
            selectedEssayFiles: [],
            isUploading: false,
            knowledgeUploadProgress: '',
            knowledgeUploadError: '',
            essayUploadProgress: '',
            essayUploadError: '',
            token: localStorage.getItem('accessToken') || '',
            locale: localStorage.getItem('locale') === 'en' ? 'en' : 'zh',
            currentUser: null,
            authMode: 'login',
            authForm: {
                username: '',
                password: '',
                role: 'user',
                admin_code: ''
            },
            authLoading: false
        };
    },
    computed: {
        isAuthenticated() {
            return !!this.token && !!this.currentUser;
        },
        isAdmin() {
            return this.currentUser?.role === 'admin';
        },
        userInitial() {
            return (this.currentUser?.username || 'P').slice(0, 1).toUpperCase();
        },
        topThemes() {
            return TOP_THEMES[this.locale] || TOP_THEMES.zh;
        },
        displayDailyQuote() {
            return normalizeDailyQuote(this.dailyQuote, this.locale);
        },
        chatSuggestions() {
            return CHAT_SUGGESTIONS[this.locale] || CHAT_SUGGESTIONS.zh;
        },
        currentSearchPlaceholder() {
            if (this.currentView === 'knowledge_base') return this.t('common.searchKnowledge');
            if (this.currentView === 'reflections') return this.t('common.searchEssays');
            if (this.currentView === 'ai_explorer') return this.t('common.searchInsights');
            return this.t('common.searchReflections');
        },
        filteredEssays() {
            const query = this.globalSearch.trim().toLowerCase();
            if (!query) return this.essays;
            return this.essays.filter((essay) => {
                const title = this.essayDisplayTitle(essay).toLowerCase();
                return title.includes(query) || (essay.filename || '').toLowerCase().includes(query);
            });
        },
        filteredDocuments() {
            const query = this.globalSearch.trim().toLowerCase();
            if (!query) return this.documents;
            return this.documents.filter((doc) => (doc.filename || '').toLowerCase().includes(query));
        },
        filteredSessions() {
            const query = this.globalSearch.trim().toLowerCase();
            if (!query) return this.sessions;
            return this.sessions.filter((session) => {
                const title = this.sessionDisplayTitle(session).toLowerCase();
                const label = sessionLabel(session.session_id).toLowerCase();
                return title.includes(query) || label.includes(query) || (session.session_id || '').toLowerCase().includes(query);
            });
        },
        knowledgeCoveragePercent() {
            const total = this.documents.length + this.essays.length;
            if (!total) return 0;
            return Math.round((this.documents.length / total) * 100);
        },
        recentEssays() {
            return this.essays.slice(0, 3);
        },
        latestSession() {
            return this.sessions[0] || null;
        },
        insightActivity() {
            return (this.insights.activity || []).slice(-7);
        },
        insightRecentEssays() {
            return this.insights.recent_essays || [];
        },
        insightRecentSessions() {
            return this.insights.recent_sessions || [];
        },
        timelineDayCount() {
            return this.timelineGroups.length;
        },
        timelineEventCount() {
            return this.timelineGroups.reduce((total, group) => total + ((group && group.items && group.items.length) || 0), 0);
        }
    },
    async mounted() {
        this.configureMarked();
        this.applyLocale();
        if (this.token) {
            try {
                await this.fetchMe();
                await this.loadInitialWorkspaceData();
            } catch (_) {
                this.handleLogout();
            }
        }
    },
    methods: {
        essayTitle,
        sessionLabel,

        t(path, params = {}) {
            const source = TRANSLATIONS[this.locale] || TRANSLATIONS.zh;
            const value = path.split('.').reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : null), source);
            if (typeof value !== 'string') {
                return path;
            }
            return Object.entries(params).reduce(
                (message, [key, replacement]) => message.replaceAll(`{${key}}`, replacement),
                value
            );
        },

        sessionDisplayTitle(session) {
            return (session && session.title) || this.t('chat.sessionTitleFallback');
        },

        essayDisplayTitle(essay) {
            return (essay && essay.title) || this.essayTitle(essay?.filename);
        },

        normalizeViewName(view) {
            return VIEW_ALIASES[view] || view;
        },

        applyLocale() {
            document.documentElement.lang = this.locale === 'zh' ? 'zh-CN' : 'en';
            document.title = this.t('app.name');
        },

        toggleLocale() {
            this.locale = this.locale === 'zh' ? 'en' : 'zh';
        },

        async fetchDailyQuote() {
            if (!this.isAuthenticated) {
                this.dailyQuote = normalizeDailyQuote(null, this.locale);
                return;
            }

            this.dailyQuoteLoading = true;
            try {
                const response = await this.authFetch(`/daily-quote?locale=${encodeURIComponent(this.locale)}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch daily quote');
                }
                this.dailyQuote = normalizeDailyQuote(await response.json(), this.locale);
            } catch (_) {
                this.dailyQuote = normalizeDailyQuote(null, this.locale);
            } finally {
                this.dailyQuoteLoading = false;
            }
        },

        configureMarked() {
            if (!window.marked) return;
            window.marked.setOptions({
                highlight(code, lang) {
                    if (!window.hljs) return code;
                    const language = window.hljs.getLanguage(lang) ? lang : 'plaintext';
                    return window.hljs.highlight(code, { language }).value;
                },
                langPrefix: 'hljs language-',
                breaks: true,
                gfm: true
            });
        },

        parseMarkdown(text) {
            if (!window.marked) {
                return this.escapeHtml(text || '').replace(/\n/g, '<br>');
            }
            return window.marked.parse(text || '');
        },

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        },

        formatDate(value) {
            if (!value) return this.t('common.justNow');
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) return value;
            return date.toLocaleString(this.locale === 'zh' ? 'zh-CN' : 'en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        displayEssayDate(essay) {
            return this.formatDate(essay?.uploaded_at || '');
        },

        inferEssayFileType(filename) {
            const lower = String(filename || '').toLowerCase();
            if (lower.endsWith('.pdf')) return 'PDF';
            if (lower.endsWith('.doc') || lower.endsWith('.docx')) return 'Word';
            if (lower.endsWith('.xls') || lower.endsWith('.xlsx')) return 'Excel';
            if (lower.endsWith('.md') || lower.endsWith('.markdown')) return 'Markdown';
            return 'Document';
        },

        applyEssayUploadResults(items = []) {
            const now = new Date().toISOString();
            const existing = new Map((this.essays || []).map((essay) => [essay.filename, essay]));

            items.forEach((item) => {
                const filename = item?.filename;
                if (!filename) return;
                existing.set(filename, {
                    ...(existing.get(filename) || {}),
                    essay_id: item.essay_id || existing.get(filename)?.essay_id || '',
                    title: item.title || existing.get(filename)?.title || this.essayTitle(filename),
                    filename,
                    file_type: item.file_type || existing.get(filename)?.file_type || this.inferEssayFileType(filename),
                    language: item.language || existing.get(filename)?.language || '',
                    chunk_count: item.chunks_processed || existing.get(filename)?.chunk_count || 0,
                    uploaded_at: existing.get(filename)?.uploaded_at || now,
                });
            });

            this.essays = Array.from(existing.values()).sort((a, b) => {
                const left = new Date(b?.uploaded_at || 0).getTime();
                const right = new Date(a?.uploaded_at || 0).getTime();
                return left - right;
            });
        },

        removeLocalEssay(filename) {
            this.essays = (this.essays || []).filter((essay) => essay.filename !== filename);
        },

        revokeDocumentCoverUrls(documents = this.documents) {
            (documents || []).forEach((doc) => {
                if (doc && doc.preview_url) {
                    URL.revokeObjectURL(doc.preview_url);
                }
            });
        },

        async attachDocumentCoverPreview(doc) {
            if (!doc?.cover_url) {
                return doc;
            }

            try {
                const response = await this.authFetch(doc.cover_url);
                if (!response.ok) {
                    return { ...doc, preview_url: '' };
                }

                const blob = await response.blob();
                return {
                    ...doc,
                    preview_url: URL.createObjectURL(blob)
                };
            } catch (error) {
                return { ...doc, preview_url: '' };
            }
        },

        async hydrateDocumentCovers(documents = []) {
            return Promise.all((documents || []).map((doc) => this.attachDocumentCoverPreview(doc)));
        },

        clearEssaySession() {
            this.activeEssayId = '';
            this.activeEssayTitle = '';
            this.analysisMode = 'general';
        },

        bindEssaySession(essay, { startNewSession = false } = {}) {
            if (startNewSession) {
                this.messages = [];
                this.sessionId = `session_${Date.now()}`;
            }
            this.activeEssayId = essay?.essay_id || '';
            this.activeEssayTitle = this.essayDisplayTitle(essay);
            this.analysisMode = (this.activeEssayId || this.activeEssayTitle) ? 'essay' : 'general';
        },

        shortChunkText(text) {
            const value = (text || '').trim();
            if (value.length <= 180) return value || this.t('chat.noExcerpt');
            return `${value.slice(0, 177)}...`;
        },

        themeCountLabel(theme) {
            const count = Number(theme?.count || 0);
            return this.locale === 'zh' ? `${count} 次出现` : `${count} mentions`;
        },

        timelineKindLabel(kind) {
            const labels = this.locale === 'zh'
                ? { essay: '随笔', session: '会话', document: '知识' }
                : { essay: 'Essay', session: 'Session', document: 'Knowledge' };
            return labels[kind] || kind;
        },

        timelineCtaLabel(item) {
            if (item?.kind === 'essay') return this.locale === 'zh' ? '在 AI 中展开' : 'Open in AI';
            if (item?.kind === 'session') return this.locale === 'zh' ? '继续会话' : 'Resume session';
            return this.locale === 'zh' ? '查看知识库' : 'Open library';
        },

        activityBarStyle(value) {
            const height = Math.max(12, Math.min(72, Number(value || 0) * 18));
            return { height: `${height}px` };
        },

        authHeaders(extra = {}) {
            const headers = { ...extra };
            if (this.token) {
                headers.Authorization = `Bearer ${this.token}`;
            }
            return headers;
        },

        async authFetch(url, options = {}) {
            const opts = { ...options };
            opts.headers = this.authHeaders(opts.headers || {});
            const response = await fetch(url, opts);
            if (response.status === 401) {
                this.handleLogout();
                throw new Error(this.t('common.authExpired'));
            }
            return response;
        },

        async fetchMe() {
            const response = await this.authFetch('/auth/me');
            if (!response.ok) {
                throw new Error(this.t('common.authFailed'));
            }
            this.currentUser = await response.json();
        },

        async loadInitialWorkspaceData() {
            await this.loadSessions({ silent: true });
            await this.loadEssays({ silent: true });
            await this.fetchDailyQuote();
            if (this.isAdmin) {
                await this.loadDocuments({ silentForbidden: true });
            }
        },

        async handleAuthSubmit() {
            if (this.authLoading) return;

            const username = this.authForm.username.trim();
            const password = this.authForm.password.trim();
            if (!username || !password) {
                alert(this.t('common.usernamePasswordRequired'));
                return;
            }

            this.authLoading = true;
            try {
                const endpoint = this.authMode === 'login' ? '/auth/login' : '/auth/register';
                const payload = { username, password };

                if (this.authMode === 'register') {
                    payload.role = this.authForm.role;
                    payload.admin_code = this.authForm.admin_code || null;
                }

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(data.detail || this.t('common.authFailed'));
                }

                this.token = data.access_token;
                this.currentUser = { username: data.username, role: data.role };
                localStorage.setItem('accessToken', this.token);
                this.authForm.password = '';
                this.authForm.admin_code = '';
                this.currentView = 'dashboard';
                this.globalSearch = '';
                this.messages = [];
                this.sessionId = `session_${Date.now()}`;
                this.clearEssaySession();
                await this.loadInitialWorkspaceData();
            } catch (error) {
                alert(error.message);
            } finally {
                this.authLoading = false;
            }
        },

        handleLogout() {
            if (this.abortController) {
                this.abortController.abort();
            }
            this.revokeDocumentCoverUrls();
            this.token = '';
            this.currentUser = null;
            this.abortController = null;
            this.isLoading = false;
            this.messages = [];
            this.sessions = [];
            this.documents = [];
            this.essays = [];
            this.insights = { ...emptyInsights() };
            this.insightsLoading = false;
            this.timelineGroups = [];
            this.timelineLoading = false;
            this.selectedKnowledgeFiles = [];
            this.selectedEssayFiles = [];
            this.globalSearch = '';
            this.currentView = 'dashboard';
            this.sessionId = `session_${Date.now()}`;
            this.userInput = '';
            this.clearEssaySession();
            this.dailyQuote = defaultDailyQuote(this.locale);
            this.dailyQuoteLoading = false;
            this.knowledgeUploadProgress = '';
            this.knowledgeUploadError = '';
            this.essayUploadProgress = '';
            this.essayUploadError = '';
            localStorage.removeItem('accessToken');
        },

        setCurrentView(view) {
            if (!this.isAuthenticated) return;
            const nextView = this.normalizeViewName(view);
            if (nextView === 'knowledge_base' && !this.isAdmin) {
                this.currentView = 'dashboard';
                return;
            }
            this.currentView = nextView;
            if (nextView === 'knowledge_base') this.loadDocuments({ silentForbidden: true });
            if (nextView === 'reflections') this.loadEssays({ silent: true });
            if (nextView === 'ai_explorer') this.loadSessions({ silent: true });
            if (nextView === 'insights') this.loadInsights({ silent: true });
            if (nextView === 'timeline') this.loadTimeline({ silent: true });
        },

        startNewReflection() {
            this.handleNewChat();
            this.setCurrentView('ai_explorer');
            this.focusComposer();
        },

        focusComposer() {
            this.$nextTick(() => {
                if (this.$refs.textarea) {
                    this.$refs.textarea.focus();
                }
            });
        },

        applyChatSuggestion(prompt) {
            this.currentView = 'ai_explorer';
            this.userInput = prompt;
            this.focusComposer();
            this.$nextTick(() => {
                if (this.$refs.textarea) {
                    this.autoResize({ target: this.$refs.textarea });
                }
            });
        },

        openEssayInChat(essay) {
            this.currentView = 'ai_explorer';
            this.bindEssaySession(essay, { startNewSession: true });
            this.userInput = this.t('common.askAnalyzeEssay', { title: this.essayDisplayTitle(essay) });
            this.focusComposer();
            this.$nextTick(() => {
                if (this.$refs.textarea) {
                    this.autoResize({ target: this.$refs.textarea });
                }
            });
        },

        async openTimelineItem(item) {
            if (!item) return;

            if (item.kind === 'session' && item.reference) {
                this.loadSession(item.reference);
                return;
            }

            if (item.kind === 'essay') {
                const essay = (this.essays || []).find((candidate) =>
                    candidate.essay_id === item.reference ||
                    candidate.filename === item.reference ||
                    this.essayDisplayTitle(candidate) === item.title
                );
                if (essay) {
                    this.openEssayInChat(essay);
                    return;
                }
                this.setCurrentView('reflections');
                return;
            }

            if (item.kind === 'document') {
                this.setCurrentView('knowledge_base');
            }
        },

        handleCompositionStart() {
            this.isComposing = true;
        },

        handleCompositionEnd() {
            this.isComposing = false;
        },

        handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey && !this.isComposing) {
                event.preventDefault();
                this.handleSend();
            }
        },

        handleStop() {
            if (this.abortController) {
                this.abortController.abort();
            }
        },

        async handleSend() {
            if (!this.isAuthenticated) {
                alert(this.t('common.loginRequired'));
                return;
            }

            const text = this.userInput.trim();
            if (!text || this.isLoading || this.isComposing) return;

            this.currentView = 'ai_explorer';
            this.messages.push({
                text,
                isUser: true
            });

            this.userInput = '';
            this.$nextTick(() => {
                this.resetTextareaHeight();
                this.scrollToBottom();
            });

            this.isLoading = true;
            this.messages.push({
                text: '',
                isUser: false,
                isThinking: true,
                ragTrace: null
            });
            const botMsgIdx = this.messages.length - 1;

            this.abortController = new AbortController();

            try {
                const response = await this.authFetch('/chat/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        session_id: this.sessionId,
                        active_essay_id: this.activeEssayId,
                        active_essay_title: this.activeEssayTitle,
                        analysis_mode: this.analysisMode
                    }),
                    signal: this.abortController.signal
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                if (!response.body) {
                    throw new Error(this.t('common.browserStreamUnsupported'));
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });

                    let eventEndIndex;
                    while ((eventEndIndex = buffer.indexOf('\n\n')) !== -1) {
                        const eventStr = buffer.slice(0, eventEndIndex);
                        buffer = buffer.slice(eventEndIndex + 2);

                        if (!eventStr.startsWith('data: ')) {
                            continue;
                        }

                        const dataStr = eventStr.slice(6);
                        if (dataStr === '[DONE]') {
                            continue;
                        }

                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'content') {
                                if (this.messages[botMsgIdx].isThinking) {
                                    this.messages[botMsgIdx].isThinking = false;
                                }
                                this.messages[botMsgIdx].text += data.content;
                            } else if (data.type === 'trace') {
                                this.messages[botMsgIdx].ragTrace = data.rag_trace || null;
                            } else if (data.type === 'error') {
                                this.messages[botMsgIdx].isThinking = false;
                                this.messages[botMsgIdx].text = data.content || this.t('chat.processingFailed');
                            }
                        } catch (parseError) {
                            console.warn('SSE parse error:', parseError);
                        }
                    }

                    this.$nextTick(() => this.scrollToBottom());
                }

                await this.loadSessions({ silent: true });
            } catch (error) {
                if (error.name === 'AbortError') {
                    this.messages[botMsgIdx].isThinking = false;
                    this.messages[botMsgIdx].text = this.messages[botMsgIdx].text || this.t('chat.aborted');
                } else {
                    this.messages[botMsgIdx].isThinking = false;
                    this.messages[botMsgIdx].text = this.t('chat.unavailable', { message: error.message });
                }
            } finally {
                this.isLoading = false;
                this.abortController = null;
                this.$nextTick(() => this.scrollToBottom());
            }
        },

        autoResize(event) {
            const textarea = event.target;
            textarea.style.height = 'auto';
            textarea.style.height = `${textarea.scrollHeight}px`;
        },

        resetTextareaHeight() {
            if (this.$refs.textarea) {
                this.$refs.textarea.style.height = 'auto';
            }
        },

        scrollToBottom() {
            if (this.$refs.assistantMessages) {
                this.$refs.assistantMessages.scrollTop = this.$refs.assistantMessages.scrollHeight;
            }
        },

        handleNewChat() {
            if (!this.isAuthenticated) return;
            this.messages = [];
            this.sessionId = `session_${Date.now()}`;
            this.userInput = '';
            this.clearEssaySession();
            this.focusComposer();
        },

        async loadSessions({ silent = false } = {}) {
            if (!this.isAuthenticated) return;
            try {
                const response = await this.authFetch('/sessions');
                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || this.t('common.loadSessionsFallback'));
                }
                const data = await response.json();
                this.sessions = data.sessions || [];
            } catch (error) {
                if (!silent) {
                    alert(this.t('common.loadSessionsFailed', { message: error.message }));
                }
            }
        },

        async loadInsights({ silent = false } = {}) {
            if (!this.isAuthenticated) return;
            this.insightsLoading = true;
            try {
                const response = await this.authFetch('/insights');
                if (!response.ok) {
                    throw new Error(this.locale === 'zh' ? '无法加载洞察' : 'Unable to load insights');
                }
                this.insights = await response.json();
            } catch (error) {
                if (!silent) {
                    alert(error.message);
                }
            } finally {
                this.insightsLoading = false;
            }
        },

        async loadTimeline({ silent = false } = {}) {
            if (!this.isAuthenticated) return;
            this.timelineLoading = true;
            try {
                const response = await this.authFetch('/timeline');
                if (!response.ok) {
                    throw new Error(this.locale === 'zh' ? '无法加载时间线' : 'Unable to load timeline');
                }
                const payload = await response.json();
                this.timelineGroups = payload.groups || [];
            } catch (error) {
                if (!silent) {
                    alert(error.message);
                }
            } finally {
                this.timelineLoading = false;
            }
        },

        async loadSession(sessionId) {
            this.sessionId = sessionId;
            this.currentView = 'ai_explorer';

            try {
                const response = await this.authFetch(`/sessions/${encodeURIComponent(sessionId)}`);
                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || this.t('common.loadSessionFallback'));
                }
                const data = await response.json();
                this.messages = (data.messages || []).map((msg) => ({
                    text: msg.content,
                    isUser: msg.type === 'human',
                    ragTrace: msg.rag_trace || null,
                    isThinking: false
                }));
                this.activeEssayId = data.active_essay_id || '';
                this.activeEssayTitle = data.active_essay_title || '';
                this.analysisMode = data.analysis_mode || ((this.activeEssayId || this.activeEssayTitle) ? 'essay' : 'general');
                this.$nextTick(() => this.scrollToBottom());
            } catch (error) {
                alert(this.t('common.loadSessionFailed', { message: error.message }));
                this.messages = [];
                this.clearEssaySession();
            }
        },

        async loadDocuments({ silentForbidden = false } = {}) {
            if (!this.isAdmin) {
                this.revokeDocumentCoverUrls();
                this.documents = [];
                return;
            }
            this.documentsLoading = true;
            try {
                const response = await this.authFetch('/documents');
                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || this.t('common.loadKnowledgeFallback'));
                }
                const data = await response.json();
                const hydratedDocuments = await this.hydrateDocumentCovers(data.documents || []);
                this.revokeDocumentCoverUrls();
                this.documents = hydratedDocuments;
            } catch (error) {
                if (!(silentForbidden && /权限|permission|forbidden/i.test(error.message))) {
                    alert(this.t('common.loadKnowledgeFailed', { message: error.message }));
                }
            } finally {
                this.documentsLoading = false;
            }
        },

        async loadEssays({ silent = false } = {}) {
            if (!this.isAuthenticated) return;
            this.essaysLoading = true;
            try {
                const response = await this.authFetch('/essays');
                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || this.t('common.loadEssaysFallback'));
                }
                const data = await response.json();
                this.essays = data.essays || [];
            } catch (error) {
                if (!silent) {
                    alert(this.t('common.loadEssaysFailed', { message: error.message }));
                }
            } finally {
                this.essaysLoading = false;
            }
        },

        handleKnowledgeFileSelect(event) {
            const files = event.target.files;
            this.selectedKnowledgeFiles = files ? Array.from(files) : [];
            this.knowledgeUploadProgress = '';
            this.knowledgeUploadError = '';
            if (this.selectedKnowledgeFiles.length) {
                this.uploadKnowledgeDocument();
            }
        },

        handleEssayFileSelect(event) {
            const files = event.target.files;
            this.selectedEssayFiles = files ? Array.from(files) : [];
            this.essayUploadProgress = '';
            this.essayUploadError = '';
            if (this.selectedEssayFiles.length) {
                this.uploadEssayDocument();
            }
        },

        async uploadStreamFiles({ files, endpoint, progressKey, errorKey, refName, onComplete }) {
            if (!files.length) {
                alert(this.t('common.uploadChooseFile'));
                return;
            }

            this.isUploading = true;
            this[progressKey] = this.t('common.preparingUpload', { count: files.length });
            this[errorKey] = '';

            try {
                const formData = new FormData();
                files.forEach((file) => {
                    formData.append('files', file);
                });

                const response = await this.authFetch(endpoint, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json().catch(() => ({}));
                    throw new Error(error.detail || 'Upload failed');
                }

                if (!response.body) {
                    throw new Error(this.t('common.browserUploadStreamUnsupported'));
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let successPayload = null;
                const fileErrors = [];

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });

                    let eventEndIndex;
                    while ((eventEndIndex = buffer.indexOf('\n\n')) !== -1) {
                        const eventStr = buffer.slice(0, eventEndIndex);
                        buffer = buffer.slice(eventEndIndex + 2);

                        if (!eventStr.startsWith('data: ')) {
                            continue;
                        }

                        const dataStr = eventStr.slice(6);
                        const data = JSON.parse(dataStr);
                        if (data.type === 'progress') {
                            this[progressKey] = data.detail || data.label || this[progressKey];
                        } else if (data.type === 'file_success') {
                            this[progressKey] = data.message || this.t('common.fileUploaded', { filename: data.filename });
                        } else if (data.type === 'file_error') {
                            fileErrors.push(data);
                            this[errorKey] = fileErrors.map((item) => `${item.filename}: ${item.content}`).join('\n');
                            this[progressKey] = this.t('common.partialUploadFailed', { count: fileErrors.length });
                        } else if (data.type === 'success') {
                            successPayload = data;
                            this[progressKey] = data.message || this.t('common.uploadComplete');
                            if (data.failure_count > 0 && data.failures) {
                                this[errorKey] = data.failures.map((item) => `${item.filename}: ${item.content}`).join('\n');
                            }
                        } else if (data.type === 'error') {
                            throw new Error(data.content || this.t('common.uploadFailed', { message: this.t('common.unknownError') }));
                        }
                    }
                }

                if (!successPayload) {
                    throw new Error(this.t('common.uploadMissingResult'));
                }

                if (typeof onComplete === 'function') {
                    await onComplete(successPayload);
                }

                if (this.$refs[refName]) {
                    this.$refs[refName].value = '';
                }

                setTimeout(() => {
                    this[progressKey] = '';
                }, 3000);
            } catch (error) {
                this[errorKey] = error.message;
                this[progressKey] = this.t('common.uploadFailed', { message: error.message });
            } finally {
                this.isUploading = false;
            }
        },

        async uploadKnowledgeDocument() {
            await this.uploadStreamFiles({
                files: this.selectedKnowledgeFiles,
                endpoint: '/documents/upload/stream',
                progressKey: 'knowledgeUploadProgress',
                errorKey: 'knowledgeUploadError',
                refName: 'knowledgeFileInput',
                onComplete: async () => {
                    this.selectedKnowledgeFiles = [];
                    await this.loadDocuments({ silentForbidden: true });
                }
            });
        },

        async uploadEssayDocument() {
            await this.uploadStreamFiles({
                files: this.selectedEssayFiles,
                endpoint: '/essays/upload/stream',
                progressKey: 'essayUploadProgress',
                errorKey: 'essayUploadError',
                refName: 'essayFileInput',
                onComplete: async (successPayload) => {
                    this.selectedEssayFiles = [];
                    await this.loadEssays({ silent: true });
                    this.applyEssayUploadResults(successPayload.files || []);
                }
            });
        },

        async deleteDocument(filename) {
            if (!confirm(this.t('common.deleteDocumentConfirm', { filename }))) {
                return;
            }

            try {
                const response = await this.authFetch(`/documents/${encodeURIComponent(filename)}`, {
                    method: 'DELETE'
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(data.detail || this.t('knowledge.delete'));
                }
                await this.loadDocuments({ silentForbidden: true });
            } catch (error) {
                alert(this.t('common.deleteDocumentFailed', { message: error.message }));
            }
        },

        async deleteEssay(filename) {
            if (!confirm(this.t('common.deleteEssayConfirm', { filename }))) {
                return;
            }

            try {
                const deletingEssay = (this.essays || []).find((essay) => essay.filename === filename) || null;
                const response = await this.authFetch(`/essays/${encodeURIComponent(filename)}`, {
                    method: 'DELETE'
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(data.detail || this.t('essays.delete'));
                }
                await this.loadEssays({ silent: true });
                this.removeLocalEssay(filename);
                if (deletingEssay && (deletingEssay.essay_id === this.activeEssayId || deletingEssay.filename === filename)) {
                    this.clearEssaySession();
                }
            } catch (error) {
                alert(this.t('common.deleteEssayFailed', { message: error.message }));
            }
        },

        async deleteSession(sessionId) {
            if (!confirm(this.t('chat.deleteConfirm'))) {
                return;
            }

            try {
                const response = await this.authFetch(`/sessions/${encodeURIComponent(sessionId)}`, {
                    method: 'DELETE'
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(data.detail || this.t('chat.deleteSession'));
                }

                if (this.sessionId === sessionId) {
                    this.handleNewChat();
                }
                await this.loadSessions({ silent: true });
            } catch (error) {
                alert(this.t('chat.deleteFailed', { message: error.message }));
            }
        }
    },
    watch: {
        messages: {
            handler() {
                this.$nextTick(() => {
                    this.scrollToBottom();
                });
            },
            deep: true
        },
        locale: {
            async handler(value) {
                localStorage.setItem('locale', value);
                this.applyLocale();
                this.dailyQuote = normalizeDailyQuote(null, value);
                if (this.isAuthenticated) {
                    await this.fetchDailyQuote();
                }
            }
        }
    }
}).mount('#app');
