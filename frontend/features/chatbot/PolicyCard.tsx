// features/chatbot/PolicyCard.tsx
import type { PolicyCard } from "./chatbot.types";

const ELIGIBILITY_BADGE: Record<string, { label: string; className: string }> = {
  eligible:   { label: "✅ 신청 가능",  className: "bg-green-50 text-green-700 border-green-200" },
  ineligible: { label: "❌ 조건 불충족", className: "bg-red-50 text-red-600 border-red-200" },
  uncertain:  { label: "⚠️ 확인 필요",  className: "bg-yellow-50 text-yellow-700 border-yellow-200" },
};

function DdayBadge({ dday }: { dday: number | null }) {
  if (dday === null) return null;
  if (dday < 0) return <span className="text-xs text-gray-400">마감</span>;
  if (dday === 0) return <span className="text-xs font-semibold text-red-600">D-day</span>;
  return <span className="text-xs font-semibold text-blue-600">D-{dday}</span>;
}

export function PolicyCardItem({ policy }: { policy: PolicyCard }) {
  const badge = ELIGIBILITY_BADGE[policy.eligibility] ?? ELIGIBILITY_BADGE.uncertain;
  const url = policy.apply_url || policy.detail_url;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-1 flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-gray-900 leading-snug flex-1">
          {policy.plcy_nm || "정책명 없음"}
        </p>
        <DdayBadge dday={policy.dday} />
      </div>

      {policy.category && (
        <span className="inline-block mb-2 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700">
          {policy.category}
        </span>
      )}

      {policy.summary && (
        <p className="mb-3 text-xs text-gray-600 leading-relaxed line-clamp-2">
          {policy.summary}
        </p>
      )}

      <div className="flex items-center justify-between gap-2">
        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${badge.className}`}>
          {badge.label}
        </span>

        {url ? (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-blue-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition"
          >
            자세히 보기 →
          </a>
        ) : (
          <span className="text-xs text-gray-400">링크 없음</span>
        )}
      </div>

      {policy.eligibility === "ineligible" && policy.ineligible_reasons.length > 0 && (
        <p className="mt-2 text-[11px] text-red-500 leading-relaxed">
          {policy.ineligible_reasons.join(" · ")}
        </p>
      )}
    </div>
  );
}
