const { createApp } = Vue;

// 前端是 Vue 3 CDN 单页应用：常量区负责文案/默认数据，createApp 内部负责状态和交互。
const TOP_THEMES = {
    zh: ['存在主义', '斯多葛主义', '荒诞', '决定论', '伦理'],
    en: ['Existentialism', 'Stoicism', 'Absurdity', 'Determinism', 'Ethics']
};

const CHAT_SUGGESTIONS = {
    zh: [
        '陪我看看这背后真正被触动的地方。',
        '帮我理解这件事可能在保护我什么。',
        '把我的价值感和现实安排之间的张力慢慢说清楚。'
    ],
    en: [
        'Help me notice what this is really touching in me.',
        'Help me understand what this pattern may be protecting.',
        'Gently unpack the tension between my values and my schedule.'
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
            subtitle: '安静的心绪花园',
            authCopy: '把随笔、阅读与对话安放在一个更温柔的自我回看空间。',
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
            dashboard: '今日',
            knowledge_base: '参考资料',
            reflections: '反思花园',
            ai_explorer: '陪伴式回看',
            insights: '回声',
            timeline: '时间线',
            knowledge: '参考资料',
            essays: '反思花园',
            chat: '陪伴式回看',
            settings: '设置'
        },
        profile: {
            admin: '管理员策展人',
            user: '自我探索用户',
            logout: '退出登录'
        },
        dashboard: {
            quoteLoading: '正在获取今日治愈语句...',
            totalEssays: '写下的心绪',
            topThemes: '反复出现的主题',
            knowledgeCoverage: '可参考的阅读',
            publicDocs: '份参考资料',
            privateEssays: '段心绪记录',
            deepSessions: '陪伴回看',
            startSession: '开始回看',
            recentEssays: '最近的心绪',
            viewAll: '查看全部',
            emptyEssays: '上传一篇反思、随笔或 Markdown 日志，开始建立你的私人档案。',
            lastAnalysis: '最近回看的主题',
            openChat: '继续回看',
            knowledgeActive: '参考资料已安放',
            updatedMessages: '更新于 {date} · {count} 条消息',
            ready: 'The Mindful Curator 已准备好，随时陪你进入更深的反思。'
        },
        knowledge: {
            title: '知识库',
            restricted: '此区域仅对管理员开放。',
            hero: '安放心理学、哲学与其他基础文本，让它们在回看时成为安静的参照背景。',
            newUpload: '加入资料',
            dropTitle: '拖拽文档到这里',
            dropBody: '支持格式：PDF、DOCX、MD（单文件最大 50MB）',
            browse: '或浏览文件',
            loading: '正在整理资料...',
            empty: '暂时还没有可参考的资料。',
            sourceCaption: '会作为反思时的温柔参照，不替代你的原文。',
            readyForReflection: '已准备好陪伴分析',
            delete: '移除'
        },
        essays: {
            title: '你的心绪花园',
            hero: '把日记、随笔和片段安放在这里，让 AI 帮你温柔地回看反复出现的情绪、关系与价值线索。',
            newEntry: '写入新的反思',
            loading: '正在加载你的反思',
            loadingBody: '花园正在准备中。',
            empty: '花园还在等待第一颗种子',
            emptyBody: '上传一篇日记、随笔或 Markdown 片段，开始建立只属于你的反思档案。',
            analyzed: '可温柔回看',
            chunkLabel: '段心绪线索已整理好',
            delete: '移除',
            viewInsights: '展开回看'
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
            title: '陪伴式回看',
            subtitle: '我们慢慢读你的文字，靠近那些反复出现的感受、关系和价值感。',
            knowledgeActive: '知识库已启用',
            welcomeTitle: '可以从一段很小的感受开始。',
            welcomeBody: '写下最近萦绕着你的片段、一个反复出现的习惯，或者一种还没有名字的情绪。',
            thinking: '我在慢慢读你的文字...',
            references: '参考过：{filename}',
            sourcesUsed: '展开参考过的文字',
            options: '如果还想继续，我们可以顺着这里再看一点：',
            optionOrigin: '靠近更深处',
            optionGains: '看看它在保护什么',
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
            searchKnowledge: '搜索参考资料...',
            searchEssays: '搜索心绪记录...',
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
            askAnalyzeEssay: '请陪我温柔地回看这篇反思《{title}》，像写一段短文一样帮我理解它。'
        }
    },
    en: {
        app: {
            name: 'PsycheArchive',
            subtitle: 'A quiet reflection garden',
            authCopy: 'A softer space for journals, readings, and AI-guided self-reflection.',
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
            dashboard: 'Today',
            knowledge_base: 'References',
            reflections: 'Reflection Garden',
            ai_explorer: 'Guided Reflection',
            insights: 'Echoes',
            timeline: 'Timeline',
            knowledge: 'References',
            essays: 'Reflection Garden',
            chat: 'Guided Reflection',
            settings: 'Settings'
        },
        profile: {
            admin: 'Admin Curator',
            user: 'Reflective User',
            logout: 'Log Out'
        },
        dashboard: {
            quoteLoading: 'Fetching today’s healing words...',
            totalEssays: 'Reflections Kept',
            topThemes: 'Returning Themes',
            knowledgeCoverage: 'Reading Support',
            publicDocs: 'references',
            privateEssays: 'reflection notes',
            deepSessions: 'Guided Revisits',
            startSession: 'Begin Reflection',
            recentEssays: 'Recent Reflections',
            viewAll: 'View All',
            emptyEssays: 'Upload a reflection, essay, or markdown journal to start your private archive.',
            lastAnalysis: 'Recently Revisited',
            openChat: 'Keep Reflecting',
            knowledgeActive: 'References Ready',
            updatedMessages: 'Updated {date} · {count} messages',
            ready: 'The Mindful Curator is ready whenever you want to begin a deeper reflection.'
        },
        knowledge: {
            title: 'Knowledge Base',
            restricted: 'This area is reserved for admin curators.',
            hero: 'Collect psychology, philosophy, and foundational texts so they can quietly support future reflections.',
            newUpload: 'Add Source',
            dropTitle: 'Drag & Drop Documents',
            dropBody: 'Supported formats: PDF, DOCX, MD (Max 50MB per file)',
            browse: 'or browse files',
            loading: 'Preparing your sources...',
            empty: 'No reference sources yet.',
            sourceCaption: 'A gentle reference for reflection, never a replacement for your own words.',
            readyForReflection: 'Ready to support reflection',
            delete: 'Remove'
        },
        essays: {
            title: 'Your Reflection Garden',
            hero: 'Keep journals, notes, and fragments in one calm place, then let AI help you revisit recurring feelings, relationships, and values.',
            newEntry: 'Add Reflection',
            loading: 'Loading your reflections',
            loadingBody: 'The garden is being prepared.',
            empty: 'Your garden is waiting for its first seed',
            emptyBody: 'Upload a journal, essay, or markdown note to begin your private reflection archive.',
            analyzed: 'Ready to revisit',
            chunkLabel: 'reflection threads are ready',
            delete: 'Remove',
            viewInsights: 'Reflect gently'
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
            title: 'Guided Reflection',
            subtitle: 'A slower reading of your words, feelings, relationships, and values.',
            knowledgeActive: 'Knowledge Base Active',
            welcomeTitle: 'You can begin with one small feeling.',
            welcomeBody: 'Share a recent fragment, a recurring habit, or an emotion that does not have a clear name yet.',
            thinking: 'I am reading your words slowly...',
            references: 'Revisited: {filename}',
            sourcesUsed: 'Open the passages I referenced',
            options: 'If you want to continue, we can stay with one thread:',
            optionOrigin: 'Move closer to it',
            optionGains: 'See what it protects',
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
            searchKnowledge: 'Search references...',
            searchEssays: 'Search reflections...',
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
            askAnalyzeEssay: 'Please help me gently revisit the reflection "{title}" as a warm, essay-like response.'
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

// 后端聊天和上传都通过 Server-Sent Events 推送进度；统一读取逻辑避免两处手写缓冲解析。
async function consumeSseMessages(response, onMessage, { onParseError = null } = {}) {
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

            let payload;
            try {
                payload = JSON.parse(dataStr);
            } catch (error) {
                if (typeof onParseError === 'function') {
                    onParseError(error, dataStr);
                    continue;
                }
                throw error;
            }
            await onMessage(payload);
        }
    }
}

createApp({
    data() {
        return {
            // 对话状态
            messages: [],
            userInput: '',
            isLoading: false,
            abortController: null,
            sessionId: `session_${Date.now()}`,
            activeEssayId: '',
            activeEssayTitle: '',
            analysisMode: 'general',
            // 工作台数据
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
            // 登录与本地偏好
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

        documentSourceLabel(doc) {
            const type = String(doc?.file_type || doc?.filename || '').toLowerCase();
            if (this.locale === 'zh') {
                if (type.includes('pdf')) return '阅读资料';
                if (type.includes('doc') || type.includes('word')) return '手稿资料';
                if (type.includes('md') || type.includes('markdown')) return '文字资料';
                return '参考资料';
            }
            if (type.includes('pdf')) return 'Reading source';
            if (type.includes('doc') || type.includes('word')) return 'Manuscript source';
            if (type.includes('md') || type.includes('markdown')) return 'Text source';
            return 'Reference source';
        },

        essaySourceLabel(essay) {
            const type = String(essay?.file_type || essay?.filename || '').toLowerCase();
            if (this.locale === 'zh') {
                if (type.includes('md') || type.includes('markdown')) return '日记片段';
                if (type.includes('pdf')) return '长文记录';
                if (type.includes('doc') || type.includes('word')) return '手稿记录';
                if (type.includes('xls') || type.includes('excel')) return '整理记录';
                return '心绪记录';
            }
            if (type.includes('md') || type.includes('markdown')) return 'Journal note';
            if (type.includes('pdf')) return 'Longform reflection';
            if (type.includes('doc') || type.includes('word')) return 'Draft reflection';
            if (type.includes('xls') || type.includes('excel')) return 'Organized note';
            return 'Reflection note';
        },

        essayReflectionSummary(essay) {
            const title = this.essayDisplayTitle(essay);
            if (this.locale === 'zh') {
                return title
                    ? '已经整理成可回顾的反思脉络，适合慢慢重新靠近。'
                    : '一段已经沉淀的心绪记录，适合慢慢回看。';
            }
            return title
                ? 'Organized into a reflection thread you can revisit at your own pace.'
                : 'A settled reflection is ready for a gentler revisit.';
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
            const html = window.marked.parse(text || '');
            if (!window.DOMPurify) {
                return this.escapeHtml(text || '').replace(/\n/g, '<br>');
            }
            return window.DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
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
                // 封面接口需要鉴权，先用带 token 的请求拿到 blob，再转成浏览器本地可渲染的 URL。
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
                this.resetWorkspaceScroll();
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
            this.resetWorkspaceScroll();
        },

        startNewReflection() {
            this.handleNewChat();
            this.setCurrentView('ai_explorer');
            this.focusComposer();
        },

        resetWorkspaceScroll() {
            this.$nextTick(() => {
                const scrollOptions = { top: 0, left: 0, behavior: 'auto' };
                const scrollingElement = document.scrollingElement || document.documentElement;
                if (scrollingElement) {
                    scrollingElement.scrollTo(scrollOptions);
                }

                const activePane = document.querySelector('.psyche-canvas, .psyche-chat-layout');
                if (activePane && typeof activePane.scrollTo === 'function') {
                    activePane.scrollTo(scrollOptions);
                }
            });
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

                await consumeSseMessages(
                    response,
                    async (data) => {
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
                        this.$nextTick(() => this.scrollToBottom());
                    },
                    {
                        onParseError(parseError) {
                            console.warn('SSE parse error:', parseError);
                        }
                    }
                );

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
            if (!textarea) return;
            textarea.style.height = '';
            textarea.style.overflowY = textarea.scrollHeight > textarea.clientHeight ? 'auto' : 'hidden';
        },

        resetTextareaHeight() {
            if (this.$refs.textarea) {
                this.$refs.textarea.style.height = '';
                this.$refs.textarea.style.overflowY = 'hidden';
                this.$refs.textarea.scrollTop = 0;
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

                let successPayload = null;
                const fileErrors = [];

                await consumeSseMessages(response, async (data) => {
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
                });

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
