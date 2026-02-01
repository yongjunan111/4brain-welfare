// features/chatbot/ChatWindow.tsx
"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useChatbotStore } from "@/stores/chatbot.store";
import { useProfileStore } from "@/stores/profile.store";
import { ChatMessageBubble } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

// 취업상태 라벨 매핑
const JOB_STATUS_LABELS: Record<string, string> = {
  none: "제한없음",
  worker: "재직자",
  self_employed: "자영업자",
  unemployed: "미취업자",
  freelancer: "프리랜서",
  daily_worker: "일용근로자",
  startup_preparing: "(예비)창업자",
  short_term_worker: "단기근로자",
  other: "기타",
};

export function ChatWindow() {
  const messages = useChatbotStore((s) => s.messages);
  const profile = useProfileStore((s) => s.profile);
  const fetchProfile = useProfileStore((s) => s.fetchProfile);

  // 컴포넌트 마운트 시 프로필 불러오기
  useEffect(() => {
    if (!profile) {
      fetchProfile();
    }
  }, [profile, fetchProfile]);

  // 소득 표시 포맷팅
  const formatIncome = () => {
    if (!profile) return "-";
    const { incomeMin, incomeMax } = profile;
    if (incomeMin == null && incomeMax == null) return "-";
    if (incomeMin != null && incomeMax != null) {
      return `${incomeMin}~${incomeMax}만원`;
    }
    if (incomeMin != null) return `${incomeMin}만원 이상`;
    if (incomeMax != null) return `${incomeMax}만원 이하`;
    return "-";
  };

  // ✅ ③ 이미지 구조를 단순화한 2컬럼: (왼쪽 요약) + (오른쪽 대화)
  return (
    <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-[320px_1fr]">
      {/* 왼쪽: 사용자 정보 요약 */}
      <aside className="rounded-xl border bg-gray-50 p-4">
        <div className="text-sm font-semibold">내 정보 요약</div>
        <div className="mt-3 space-y-2 text-xs text-gray-700">
          <Row
            label="나이"
            value={profile?.age != null ? `만 ${profile.age}세` : "-"}
          />
          <Row
            label="거주지"
            value={profile?.interestDistrict || "-"}
          />
          <Row
            label="구직/재직"
            value={profile?.jobStatus ? JOB_STATUS_LABELS[profile.jobStatus] || "-" : "-"}
          />
          <Row
            label="소득"
            value={formatIncome()}
          />
        </div>

        <Link href="/mypage/profile">
          <button className="mt-4 w-full rounded-xl border bg-white px-3 py-2 text-xs hover:bg-gray-100 transition">
            내정보 업데이트
          </button>
        </Link>
      </aside>

      {/* 오른쪽: 채팅 */}
      <section className="flex min-h-[520px] flex-col rounded-xl border">
        <div className="flex-1 space-y-3 overflow-auto p-4">
          {messages.map((m) => (
            <ChatMessageBubble key={m.id} message={m} />
          ))}
        </div>

        <div className="border-t p-3">
          <ChatInput />
        </div>
      </section>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-white px-3 py-2">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

