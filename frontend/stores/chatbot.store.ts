// stores/chatbot.store.ts
import { create } from "zustand";
import { createJSONStorage, devtools, persist } from "zustand/middleware";
import type { ChatMessage } from "@/features/chatbot/chatbot.types";
import { chatbotApi } from "@/features/chatbot/chatbot.api";

interface ChatbotState {
  isOpen: boolean;
  isLoading: boolean;
  sessionId: string | null;
  sessionToken: string | null;
  messages: ChatMessage[];
  hasProfileData: boolean;
  profileInjected: boolean;
  panelWidth: number;
  panelHeight: number;
  panelX: number | null;
  panelY: number | null;

  open: () => Promise<void>;
  close: () => void;
  reset: () => void;
  resetConversation: () => Promise<void>;
  ensureSession: () => Promise<void>;
  refreshSession: () => Promise<void>;
  setProfileInjected: (value: boolean) => void;
  setPanelSize: (width: number, height: number) => void;
  setPanelPosition: (x: number, y: number) => void;

  sendMessage: (content: string, includeProfile?: boolean) => Promise<void>;
}

export const useChatbotStore = create<ChatbotState>()(
  devtools(
    persist(
      (set, get) => ({
        isOpen: false,
        isLoading: false,
        sessionId: null,
        sessionToken: null,
        messages: [],
        hasProfileData: false,
        profileInjected: false,
        panelWidth: 420,
        panelHeight: 620,
        panelX: null,
        panelY: null,

        open: async () => {
          set({ isOpen: true });
          await get().ensureSession();
        },

        close: () => set({ isOpen: false, panelX: null, panelY: null }),

        reset: () => {
          set({
            isOpen: false,
            sessionId: null,
            sessionToken: null,
            messages: [],
            isLoading: false,
            profileInjected: false,
          });
        },

        resetConversation: async () => {
          await get().refreshSession();
          set({ isOpen: true });
        },

        ensureSession: async () => {
          if (get().sessionId) return;

          try {
            set({ isLoading: true });
            const session = await chatbotApi.createSession();
            set({
              sessionId: session.id,
              sessionToken: session.sessionToken ?? null,
              messages: session.messages,
              hasProfileData: session.hasProfileData ?? false,
            });
          } catch (error) {
            console.error("Failed to create chat session:", error);
          } finally {
            set({ isLoading: false });
          }
        },

        refreshSession: async () => {
          set({
            sessionId: null,
            sessionToken: null,
            messages: [],
            hasProfileData: false,
            profileInjected: false,
            isLoading: false,
          });
          await get().ensureSession();
        },

        setProfileInjected: (value: boolean) => set({ profileInjected: value }),

        setPanelSize: (width: number, height: number) => {
          set({ panelWidth: width, panelHeight: height });
        },

        setPanelPosition: (x: number, y: number) => {
          set({ panelX: x, panelY: y });
        },

        sendMessage: async (content: string, includeProfile?: boolean) => {
          const { sessionId, sessionToken, messages } = get();
          if (!sessionId) return;

          const tempUserMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content,
            createdAt: Date.now(),
          };

          set({
            isLoading: true,
            messages: [...messages, tempUserMsg],
          });

          try {
            const response = await chatbotApi.sendMessage(
              sessionId,
              content,
              sessionToken,
              includeProfile,
            );

            set((state) => ({
              messages: [
                ...state.messages.slice(0, -1),
                response.userMessage,
                response.assistantMessage,
              ],
            }));
          } catch (error) {
            console.error("Failed to send message:", error);
          } finally {
            set({ isLoading: false });
          }
        },
      }),
      {
        name: "welfarecompass:chatbot_state",
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          sessionId: state.sessionId,
          sessionToken: state.sessionToken,
          messages: state.messages,
          hasProfileData: state.hasProfileData,
          panelWidth: state.panelWidth,
          panelHeight: state.panelHeight,
        }),
      },
    ),
  ),
);
