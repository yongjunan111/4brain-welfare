// features/mypage/mypage.api.ts
"use client";

import { MOCK_PROFILE, MOCK_VERIFY } from "./mypage.mock";
import type { MyProfile, VerifyState } from "./mypage.types";

const PROFILE_KEY = "welfarecompass:mypage_profile";
const VERIFY_KEY = "welfarecompass:verify_state";

export async function getMyProfile(): Promise<MyProfile> {
    await new Promise((r) => setTimeout(r, 60));
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return MOCK_PROFILE;
    try {
        return JSON.parse(raw) as MyProfile;
    } catch {
        return MOCK_PROFILE;
    }
}

export async function saveMyProfile(profile: MyProfile): Promise<void> {
    await new Promise((r) => setTimeout(r, 120));
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export async function getVerifyState(): Promise<VerifyState> {
    await new Promise((r) => setTimeout(r, 30));
    const raw = localStorage.getItem(VERIFY_KEY);
    if (!raw) return MOCK_VERIFY;
    try {
        return JSON.parse(raw) as VerifyState;
    } catch {
        return MOCK_VERIFY;
    }
}

export async function setVerified(): Promise<void> {
    await new Promise((r) => setTimeout(r, 150));
    const next: VerifyState = { isVerified: true, verifiedAt: new Date().toISOString() };
    localStorage.setItem(VERIFY_KEY, JSON.stringify(next));
}


export async function clearVerified(): Promise<void> {
    await new Promise((r) => setTimeout(r, 80));
    localStorage.setItem(VERIFY_KEY, JSON.stringify({ isVerified: false }));
}

// =========================================================================
// [스크랩 API]
// =========================================================================
import { api } from "@/services/axios";
import { Scrap } from "./mypage.types";

export interface ScrapListResponse {
    results: {
        id: number;
        policy: {
            plcy_no: string;
            plcy_nm: string;
            plcy_expln_cn: string;
            district: string | null;
            categories: { id: number; name: string }[];
        };
        created_at: string;
    }[];
}

/**
 * ✅ 내 스크랩 목록 조회
 */
export async function fetchScraps(): Promise<Scrap[]> {
    try {
        const response = await api.get<ScrapListResponse>("/api/accounts/scraps/");
        return response.data.results.map((item) => ({
            id: item.id,
            plcy_no: item.policy.plcy_no,
            plcy_nm: item.policy.plcy_nm,
            plcy_expln_cn: item.policy.plcy_expln_cn,
            district: item.policy.district || "전국",
            category: item.policy.categories?.[0]?.name || "기타",
            created_at: item.created_at,
        }));
    } catch (error) {
        console.error("fetchScraps error:", error);
        return [];
    }
}

/**
 * ✅ 스크랩 추가
 */
export async function addScrap(policyId: string): Promise<boolean> {
    try {
        await api.post(`/api/accounts/scraps/${policyId}/`);
        return true;
    } catch (error) {
        console.error("addScrap error:", error);
        return false;
    }
}

/**
 * ✅ 스크랩 삭제
 */
export async function removeScrap(policyId: string): Promise<boolean> {
    try {
        await api.delete(`/api/accounts/scraps/${policyId}/`);
        return true;
    } catch (error) {
        console.error("removeScrap error:", error);
        return false;
    }
}
