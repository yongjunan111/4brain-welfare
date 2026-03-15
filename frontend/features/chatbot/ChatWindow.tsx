// features/chatbot/ChatWindow.tsx
"use client";

import { useEffect, useRef, useMemo } from "react";
import Link from "next/link";
import { useChatbotStore } from "@/stores/chatbot.store";
import { useAuthStore } from "@/stores/auth.store";
import { useProfileStore } from "@/stores/profile.store";
import { ChatMessageBubble } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { JOB_STATUS_LABELS, HOUSING_TYPE_LABELS } from "./chatbot.labels";

// 사이드바를 숨기는 패널 폭 기준
const SIDEBAR_BREAKPOINT = 700;

export function ChatWindow({ panelWidth }: { panelWidth?: number }) {
  const messages = useChatbotStore((s) => s.messages);
  const isLoading = useChatbotStore((s) => s.isLoading);
  const hasProfileData = useChatbotStore((s) => s.hasProfileData);
  const sendMessage = useChatbotStore((s) => s.sendMessage);
  const ensureSession = useChatbotStore((s) => s.ensureSession);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const profile = useProfileStore((s) => s.profile);
  const fetchProfile = useProfileStore((s) => s.fetchProfile);
  const profileInjected = useChatbotStore((s) => s.profileInjected);
  const setProfileInjected = useChatbotStore((s) => s.setProfileInjected);
  const bottomRef = useRef<HTMLDivElement>(null);

  // 로그인 상태일 때만 프로필 불러오기
  useEffect(() => {
    if (isAuthenticated && !profile) {
      fetchProfile();
    }
  }, [isAuthenticated, profile, fetchProfile]);

  // 새 메시지마다 하단으로 스크롤
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // 사이드바 표시 여부
  const showSidebar = useMemo(() => {
    if (!isAuthenticated) return false;
    if (panelWidth == null) return true;
    return panelWidth >= SIDEBAR_BREAKPOINT;
  }, [isAuthenticated, panelWidth]);

  // 나이 계산
  const getAge = () => {
    if (!profile || !profile.birthYear) return null;
    return new Date().getFullYear() - profile.birthYear;
  };

  return (
    <div className={`grid h-full grid-cols-1 gap-4 p-5 ${showSidebar ? "grid-cols-[320px_1fr]" : ""}`}>
      {/* 왼쪽: 사용자 정보 요약 (로그인 + 패널 넓을 때만 표시) */}
      {showSidebar && <aside className="overflow-y-auto rounded-lg border bg-gray-50 p-4">
        <div className="text-sm font-semibold">내 정보 요약</div>
        <div className="mt-3 space-y-2 text-xs text-gray-700">
          <Row label="거주지" value={profile?.district || "-"} />
          <Row label="나이" value={getAge() != null ? `만 ${getAge()}세` : "-"} />
          <Row label="주거 형태" value={profile?.housingType ? HOUSING_TYPE_LABELS[profile.housingType] || "-" : "-"} />
          <Row label="취업 상태" value={profile?.jobStatus ? JOB_STATUS_LABELS[profile.jobStatus] || "-" : "-"} />
          <Row label="연 소득" value={profile?.incomeAmount != null ? `${profile.incomeAmount}만원` : "-"} />
          <Row label="관심 분야" value={profile?.needs?.length ? profile.needs.join(", ") : "-"} />
          <Row label="특수 조건" value={profile?.specialConditions?.length ? profile.specialConditions.join(", ") : "-"} />
        </div>

        <Link href="/mypage/profile">
          <button className="mt-4 w-full rounded-xl border bg-white px-3 py-2 text-xs hover:bg-gray-100 transition">
            내정보 업데이트
          </button>
        </Link>
      </aside>}

      {/* 오른쪽: 채팅 */}
      <section className="flex h-full min-h-0 flex-col rounded-lg border">
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((m, index) => (
            <div key={m.id}>
              <ChatMessageBubble message={m} />
              {/* 첫 번째 assistant 메시지(인사말) 뒤에 프로필 반영 버튼 */}
              {index === 0 && m.role === "assistant" && hasProfileData && (
                <div className="ml-14 mt-2">
                  <button
                    type="button"
                    disabled={profileInjected || isLoading}
                    onClick={async () => {
                      await ensureSession();
                      await sendMessage("내 프로필 정보를 기반으로 맞춤 정책을 추천해주세요.", true);
                      setProfileInjected(true);
                    }}
                    className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${profileInjected
                      ? "border border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 shadow-sm"
                      }`}
                  >
                    {profileInjected ? "✅ 내 정보가 반영되었습니다" : "내 정보 반영하기"}
                  </button>
                </div>
              )}
            </div>
          ))}
          {/* 응답 대기 중 표시 */}
          {isLoading && messages.length > 0 && <ThinkingIndicator />}
          <div ref={bottomRef} />
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
