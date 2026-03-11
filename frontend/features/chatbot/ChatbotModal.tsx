// features/chatbot/ChatbotModal.tsx
"use client";

import { useCallback, useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { useChatbotStore } from "@/stores/chatbot.store";
import { ChatWindow } from "./ChatWindow";

const VIEWPORT_GAP = 16;
const MIN_WIDTH = 340;
const MIN_HEIGHT = 420;

type DragState = {
  pointerOffsetX: number;
  pointerOffsetY: number;
};

type ResizeState = {
  startX: number;
  startY: number;
  startWidth: number;
  startHeight: number;
  panelLeft: number;
  panelTop: number;
};

export function ChatbotModal() {
  const close = useChatbotStore((s) => s.close);
  const isLoading = useChatbotStore((s) => s.isLoading);
  const resetConversation = useChatbotStore((s) => s.resetConversation);
  const panelWidth = useChatbotStore((s) => s.panelWidth);
  const panelHeight = useChatbotStore((s) => s.panelHeight);
  const panelX = useChatbotStore((s) => s.panelX);
  const panelY = useChatbotStore((s) => s.panelY);
  const setPanelSize = useChatbotStore((s) => s.setPanelSize);
  const setPanelPosition = useChatbotStore((s) => s.setPanelPosition);
  const panelRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const resizeRef = useRef<ResizeState | null>(null);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

  const clampPosition = useCallback((x: number, y: number, width: number, height: number) => {
    const maxX = Math.max(VIEWPORT_GAP, window.innerWidth - width - VIEWPORT_GAP);
    const maxY = Math.max(VIEWPORT_GAP, window.innerHeight - height - VIEWPORT_GAP);
    return {
      x: clamp(x, VIEWPORT_GAP, maxX),
      y: clamp(y, VIEWPORT_GAP, maxY),
    };
  }, []);

  useEffect(() => {
    const handleResize = () => {
      const maxWidth = Math.max(MIN_WIDTH, window.innerWidth - VIEWPORT_GAP * 2);
      const maxHeight = Math.max(MIN_HEIGHT, window.innerHeight - VIEWPORT_GAP * 2);
      const nextWidth = clamp(panelWidth, MIN_WIDTH, maxWidth);
      const nextHeight = clamp(panelHeight, MIN_HEIGHT, maxHeight);

      if (nextWidth !== panelWidth || nextHeight !== panelHeight) {
        setPanelSize(nextWidth, nextHeight);
      }

      if (panelX != null && panelY != null) {
        const nextPosition = clampPosition(panelX, panelY, nextWidth, nextHeight);
        if (nextPosition.x !== panelX || nextPosition.y !== panelY) {
          setPanelPosition(nextPosition.x, nextPosition.y);
        }
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [clampPosition, panelHeight, panelWidth, panelX, panelY, setPanelPosition, setPanelSize]);

  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      const panelEl = panelRef.current;
      if (!panelEl) return;

      if (dragRef.current) {
        const rect = panelEl.getBoundingClientRect();
        const nextPosition = clampPosition(
          event.clientX - dragRef.current.pointerOffsetX,
          event.clientY - dragRef.current.pointerOffsetY,
          rect.width,
          rect.height
        );
        setPanelPosition(nextPosition.x, nextPosition.y);
      }

      if (resizeRef.current) {
        const maxWidth = Math.max(MIN_WIDTH, window.innerWidth - resizeRef.current.panelLeft - VIEWPORT_GAP);
        const maxHeight = Math.max(MIN_HEIGHT, window.innerHeight - resizeRef.current.panelTop - VIEWPORT_GAP);
        const nextWidth = clamp(
          resizeRef.current.startWidth + (event.clientX - resizeRef.current.startX),
          MIN_WIDTH,
          maxWidth
        );
        const nextHeight = clamp(
          resizeRef.current.startHeight + (event.clientY - resizeRef.current.startY),
          MIN_HEIGHT,
          maxHeight
        );
        setPanelSize(nextWidth, nextHeight);
      }
    };

    const handlePointerUp = () => {
      dragRef.current = null;
      resizeRef.current = null;
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, [clampPosition, setPanelPosition, setPanelSize]);

  const handleDragStart = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    const rect = panelRef.current?.getBoundingClientRect();
    if (!rect) return;

    dragRef.current = {
      pointerOffsetX: event.clientX - rect.left,
      pointerOffsetY: event.clientY - rect.top,
    };
    setPanelPosition(rect.left, rect.top);
  };

  const handleResizeStart = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    const rect = panelRef.current?.getBoundingClientRect();
    if (!rect) return;

    resizeRef.current = {
      startX: event.clientX,
      startY: event.clientY,
      startWidth: rect.width,
      startHeight: rect.height,
      panelLeft: rect.left,
      panelTop: rect.top,
    };
    setPanelPosition(rect.left, rect.top);
  };

  const handleResetConversation = async () => {
    await resetConversation();
    setShowResetConfirm(false);
  };

  return (
    <div
      ref={panelRef}
      className="fixed z-50 flex rounded-sm border bg-white shadow-2xl"
      style={{
        width: panelWidth,
        height: panelHeight,
        maxWidth: `calc(100vw - ${VIEWPORT_GAP * 2}px)`,
        maxHeight: `calc(100vh - ${VIEWPORT_GAP * 2}px)`,
        ...(panelX != null && panelY != null
          ? { left: panelX, top: panelY }
          : { right: VIEWPORT_GAP, bottom: VIEWPORT_GAP }),
      }}
    >
      <div className="flex h-full w-full flex-col overflow-hidden rounded-sm">
        <div
          className="flex cursor-move items-center justify-between border-b bg-slate-50 px-4 py-3"
          onPointerDown={handleDragStart}
        >
          <div className="text-sm font-semibold">복지 상담 챗봇</div>
          <div className="flex items-center gap-2">
            {showResetConfirm ? (
              <>
                <span className="text-xs text-gray-500">초기화할까요?</span>
                <button
                  type="button"
                  onClick={handleResetConversation}
                  disabled={isLoading}
                  className="rounded-lg border border-red-300 bg-red-50 px-3 py-1 text-xs text-red-600 hover:bg-red-100 disabled:opacity-50"
                >
                  확인
                </button>
                <button
                  type="button"
                  onClick={() => setShowResetConfirm(false)}
                  className="rounded-lg border px-3 py-1 text-xs text-gray-600 hover:bg-gray-100"
                >
                  취소
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => setShowResetConfirm(true)}
                disabled={isLoading}
                className="rounded-lg border px-3 py-1 text-xs text-gray-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                초기화
              </button>
            )}
            <button
              type="button"
              onClick={close}
              className="rounded-lg border px-3 py-1 text-xs text-gray-700"
            >
              닫기
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1">
          <ChatWindow panelWidth={panelWidth} />
        </div>

        <div
          aria-label="resize"
          onPointerDown={handleResizeStart}
          className="absolute bottom-0 right-0 h-5 w-5 cursor-se-resize rounded-tl-md bg-slate-200/80"
        />
      </div>
    </div>
  );
}
