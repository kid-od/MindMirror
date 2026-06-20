"""认证路由：注册、登录、读取当前用户。"""

try:
    import api_context as ctx
except ModuleNotFoundError:
    from backend import api_context as ctx


router = ctx.APIRouter()


@router.post("/auth/register", response_model=ctx.AuthResponse)
async def register(request: ctx.RegisterRequest, db: ctx.Session = ctx.Depends(ctx.get_db)):
    username = (request.username or "").strip()
    password = (request.password or "").strip()
    if not username or not password:
        raise ctx.HTTPException(status_code=400, detail="用户名和密码不能为空")

    exists = db.query(ctx.User).filter(ctx.User.username == username).first()
    if exists:
        raise ctx.HTTPException(status_code=409, detail="用户名已存在")

    role = ctx.resolve_role(request.role, request.admin_code)
    user = ctx.User(username=username, password_hash=ctx.get_password_hash(password), role=role)
    db.add(user)
    db.commit()

    token = ctx.create_access_token(username=username, role=role)
    return ctx.AuthResponse(access_token=token, username=username, role=role)


@router.post("/auth/login", response_model=ctx.AuthResponse)
async def login(request: ctx.LoginRequest, db: ctx.Session = ctx.Depends(ctx.get_db)):
    user = ctx.authenticate_user(db, request.username, request.password)
    if not user:
        raise ctx.HTTPException(status_code=401, detail="用户名或密码错误")
    token = ctx.create_access_token(username=user.username, role=user.role)
    return ctx.AuthResponse(access_token=token, username=user.username, role=user.role)


@router.get("/auth/me", response_model=ctx.CurrentUserResponse)
async def me(current_user: ctx.User = ctx.Depends(ctx.get_current_user)):
    return ctx.CurrentUserResponse(username=current_user.username, role=current_user.role)
