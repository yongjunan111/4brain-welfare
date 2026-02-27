// features/policy/PolicySearchPageClient.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fetchPolicies } from "./policy.api";
import { Policy, PolicyCategory } from "./policy.types";
import { PolicyCard } from "./PolicyCard";
import { Pagination } from "@/components/common/Pagination";

const CATEGORY_OPTIONS: Array<{ value: PolicyCategory | "all"; label: string }> = [
    { value: "all", label: "전체" },
    { value: "job", label: "일자리" },
    { value: "housing", label: "주거" },
    { value: "education", label: "교육" },
    { value: "welfare", label: "복지·문화" },
    { value: "participation", label: "참여·권리" },
];

export function PolicySearchPageClient() {
    const searchParams = useSearchParams();

    // ✅ URL 파라미터로 초기 상태 설정
    const initialQ = searchParams.get("q") || "";
    const initialCategory = (searchParams.get("category") as PolicyCategory | "all") || "all";

    const [q, setQ] = useState(initialQ);
    const [category, setCategory] = useState<PolicyCategory | "all">(initialCategory);
    const [region, setRegion] = useState("");
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(12); // ✅ 페이지 크기 상태 추가
    const [items, setItems] = useState<Policy[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [loading, setLoading] = useState(false);

    // ✅ 검색 조건 변경 시 1페이지로 리셋
    useEffect(() => {
        setPage(1);
    }, [q, category, region, pageSize]); // pageSize 변경 시에도 리셋

    // ✅ 데이터 로드 (페이지 변경 포함)
    useEffect(() => {
        let alive = true;

        (async () => {
            setLoading(true);
            try {
                const { policies, totalCount } = await fetchPolicies({
                    q,
                    category,
                    region,
                    page,
                    page_size: pageSize, // ✅ 페이지 크기 전달
                });
                if (alive) {
                    setItems(policies);
                    setTotalCount(totalCount);
                }
            } finally {
                if (alive) setLoading(false);
            }
        })();

        return () => {
            alive = false;
        };
    }, [q, category, region, page, pageSize]);

    const countText = useMemo(() => {
        if (loading) return "불러오는 중...";
        return `총 ${totalCount}건`;
    }, [totalCount, loading]);

    return (
        <div className="mx-auto w-full max-w-[1280px] px-4 py-8">
            {/* ✅ 상단 검색 바 */}
            <section className="mb-8">
                <div className="flex w-full items-center gap-2 rounded-xl border bg-white p-3">
                    {/* ... (기존 검색 필드들) ... */}

                    {/* region */}
                    <select
                        className="h-9 rounded-lg border px-2 text-xs text-gray-700"
                        value={region}
                        onChange={(e) => setRegion(e.target.value)}
                    >
                        <option value="">전체 지역</option>
                        <option value="서울시">서울시</option>
                        <option value="전국">전국</option>
                    </select>

                    {/* category */}
                    <select
                        className="h-9 rounded-lg border px-2 text-xs text-gray-700"
                        value={category}
                        onChange={(e) => setCategory(e.target.value as any)}
                    >
                        {CATEGORY_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>

                    {/* keyword */}
                    <input
                        className="h-9 flex-1 rounded-lg border px-3 text-xs outline-none"
                        placeholder="정책명을 입력해주세요."
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                    />

                    <button
                        type="button"
                        className="h-9 rounded-lg bg-gray-800 px-4 text-xs text-white"
                        onClick={() => console.log("검색")}
                    >
                        검색
                    </button>
                </div>

                <div className="mt-2 flex items-center justify-between">
                    {/* 페이지 당 개수 선택 (좌측) */}
                    <select
                        className="h-8 rounded-lg border px-2 text-[11px] text-gray-600 outline-none"
                        value={pageSize}
                        onChange={(e) => setPageSize(Number(e.target.value))}
                    >
                        <option value={8}>8개씩 보기</option>
                        <option value={12}>12개씩 보기</option>
                        <option value={16}>16개씩 보기</option>
                        <option value={24}>24개씩 보기</option>
                    </select>

                    <div className="text-[11px] text-gray-500">
                        {countText}
                    </div>
                </div>
            </section>

            {/* ✅ 카드 리스트 */}
            <section className="w-full">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    {items.map((p) => (
                        <PolicyCard key={p.id} policy={p} />
                    ))}
                </div>

                {!loading && items.length === 0 && (
                    <div className="mt-10 text-center text-sm text-gray-500">
                        조건에 맞는 정책이 없습니다.
                    </div>
                )}
            </section>

            {/* ✅ 페이지네이션 */}
            <Pagination
                currentPage={page}
                totalCount={totalCount}
                itemsPerPage={pageSize}
                onPageChange={setPage}
            />
        </div>
    );
}
