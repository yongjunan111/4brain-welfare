// features/policy/policy.constants.ts
// 카테고리 매핑/라벨 공통 상수 (PolicyCard, policy.api.ts 등에서 공유)

import type { PolicyCategory } from "./policy.types";

/**
 * 백엔드 카테고리 이름 → 프론트엔드 PolicyCategory 매핑
 */
export const CATEGORY_NAME_MAP: Record<string, PolicyCategory> = {
    "일자리": "job",
    "주거": "housing",
    "교육": "education",
    "복지문화": "welfare",
    "참여권리": "participation",
    // Fallbacks for old data or grouped categories
    "금융": "welfare",
    "창업": "job",
    "복지": "welfare",
    "문화": "welfare",
};

/**
 * PolicyCategory → 한글 라벨
 */
export const CATEGORY_LABELS: Record<PolicyCategory, string> = {
    job: "일자리",
    housing: "주거",
    education: "교육",
    welfare: "복지·문화",
    participation: "참여·권리",
};

/**
 * 카테고리 라벨 조회 (fallback 포함)
 */
export function getCategoryLabel(category: PolicyCategory | string): string {
    if (!category) return "기타";
    // 1. 이미 올바른 영문 키인 경우 (예: "job")
    if (CATEGORY_LABELS[category as PolicyCategory]) {
        return CATEGORY_LABELS[category as PolicyCategory];
    }
    // 2. 한글 카테고리 명이 직접 들어온 경우 (예: "일자리", "복지문화")
    if (category in CATEGORY_NAME_MAP) {
        return CATEGORY_LABELS[CATEGORY_NAME_MAP[category]];
    }
    // 3. 그 외의 경우 원본 텍스트 노출 (혹은 콤마 포함된 경우)
    return category;
}
