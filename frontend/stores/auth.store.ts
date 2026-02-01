// stores/auth.store.ts
import { create } from "zustand";
import { devtools } from "zustand/middleware";

interface AuthTokens {
    access: string;
    refresh: string;
}

interface AuthState {
    isAuthenticated: boolean;
    isInitialized: boolean;

    /** 앱 시작 시 localStorage에서 토큰 확인 */
    initialize: () => void;

    /** 로그인 시 토큰 저장 + 상태 업데이트 */
    login: (tokens: AuthTokens) => void;

    /** 로그아웃 시 토큰 삭제 + 상태 초기화 */
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    devtools((set) => ({
        isAuthenticated: false,
        isInitialized: false,

        initialize: () => {
            const token = localStorage.getItem("access_token");
            set({
                isAuthenticated: !!token,
                isInitialized: true,
            });
        },

        login: (tokens: AuthTokens) => {
            localStorage.setItem("access_token", tokens.access);
            localStorage.setItem("refresh_token", tokens.refresh);
            set({ isAuthenticated: true });
        },

        logout: () => {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            set({ isAuthenticated: false });
        },
    }))
);
