# Frontend User Status Fix

## 问题描述
需要确保被禁用的账号在访问任何页面时都会被重定向到 Account Disabled 页面，而不仅仅是在访问需要认证的页面时。

## 实施的解决方案

### 1. 路由守卫改进 (`GitHub_Pages/src/router/index.js`)

**改进前的问题：**
- 只在 `requiresAuth: true` 的路由上进行用户状态检查
- 被禁用的用户可能仍能访问某些页面

**改进后的解决方案：**
- 对所有已登录用户进行状态检查，无论访问哪个页面
- 只有登录页面和注册页面豁免状态检查
- 确保用户状态信息在重定向前正确存储到 localStorage

**核心逻辑：**
```javascript
// 公共页面（不需要状态检查）
const publicPages = ['login', 'register'];
const isPublicPage = publicPages.includes(to.name);

// 已登录用户访问任何非公共页面时都检查状态
if (!isPublicPage && to.name !== 'account-disabled') {
    // 执行用户状态检查
    // 如果账号被禁用或锁定，立即重定向到 account-disabled 页面
}
```

### 2. API 响应拦截器 (`GitHub_Pages/src/api.js`)

**新增功能：**
- 添加了响应拦截器来统一处理账号被禁用的情况
- 在任何 API 调用返回账号状态信息时自动检查
- 统一处理 401 错误，区分无效令牌和被禁用账号

**核心功能：**
```javascript
// 响应拦截器检查每个API响应中的账号状态
apiClient.interceptors.response.use(
    (response) => {
        // 检查响应中的账号状态
        if (response.data?.account_status) {
            // 如果账号被禁用或锁定，自动重定向
        }
    },
    (error) => {
        // 处理401错误，区分被禁用账号和无效令牌
    }
);
```

### 3. 用户状态 Composable (`GitHub_Pages/src/utils/userStatus.js`)

**新增 `useUserStatus` composable：**
- 提供响应式的用户状态监控
- 自动在组件挂载时检查用户状态
- 可选的定期状态检查（默认30秒）
- 自动处理被禁用账号的重定向

**使用方式：**
```javascript
import { useUserStatus } from '../utils/userStatus.js';

export default {
    setup() {
        const { 
            userStatus, 
            isLoading, 
            error,
            isDisabled,
            handleLogout 
        } = useUserStatus();
        
        return {
            userStatus,
            isLoading,
            error,
            isDisabled,
            handleLogout
        };
    }
}
```

## 保护层级

现在系统有三个层级的保护：

### 第一层：路由守卫
- 在页面导航时检查用户状态
- 适用于所有已登录用户访问任何页面

### 第二层：API 拦截器
- 在每次 API 调用时检查响应中的用户状态
- 自动处理被禁用账号的错误响应

### 第三层：组件级保护
- 通过 `useUserStatus` composable 在组件中提供额外保护
- 可选的定期状态监控
- 适用于需要实时状态更新的组件

## 支持的账号状态

系统现在完整支持以下账号状态：

1. **`active`** - 账号正常活跃
2. **`disabled`** - 账号被管理员禁用
3. **`locked`** - 账号因多次失败登录而被锁定
4. **`lock_expired`** - 锁定已过期，用户可以重新尝试
5. **`no_profile`** - 用户存在但没有配置文件

## 重定向逻辑

### 被禁用账号：
- **状态：** `disabled`
- **行为：** 立即重定向到 `/account-disabled`
- **页面显示：** 账号被禁用的错误页面

### 被锁定账号：
- **状态：** `locked` 且未过期
- **行为：** 重定向到 `/account-disabled`
- **页面显示：** 账号被锁定的警告页面，显示锁定剩余时间

### 锁定过期账号：
- **状态：** `locked` 但已过期
- **行为：** 允许访问，显示"重试"按钮
- **页面显示：** 可以选择重试登录

## 用户体验改进

1. **即时反馈：** 被禁用用户立即被重定向，无需等待页面加载
2. **状态持久化：** 用户状态信息正确存储，AccountDisabledView 可以显示详细信息
3. **防止绕过：** 多层保护确保用户无法通过直接URL访问绕过限制
4. **网络容错：** 在网络错误时使用缓存的状态信息
5. **清晰的错误信息：** 根据不同的账号状态显示相应的错误信息

## 测试场景

为确保功能正常工作，应测试以下场景：

1. **被禁用用户直接访问首页**
2. **被禁用用户直接访问其他功能页面**
3. **已登录用户在使用过程中被管理员禁用**
4. **被锁定用户尝试访问任何页面**
5. **锁定过期用户的恢复流程**
6. **网络错误时的降级处理**
7. **无效令牌的处理**

## 向后兼容性

- 保持对旧版 `is_active` 字段的支持
- 对于没有 `account_status` 字段的响应，使用 `is_active` 作为后备
- 确保现有的认证流程不受影响 