import {
  type PropsWithChildren,
  createContext,
  startTransition,
  useContext,
  useEffect,
  useMemo,
  useReducer,
} from "react";

import { api, ApiError } from "../lib/api";
import type { AuthUser, StoredSession } from "../types";

type AuthStatus = "bootstrapping" | "authenticated" | "anonymous";

type AuthState = {
  status: AuthStatus;
  session: StoredSession | null;
  error: string | null;
};

type AuthContextValue = {
  status: AuthStatus;
  user: AuthUser | null;
  session: StoredSession | null;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  replaceSessionUser: (user: AuthUser) => void;
  clearError: () => void;
};

type Action =
  | { type: "BOOTSTRAP_DONE"; payload: StoredSession | null }
  | { type: "AUTH_SUCCESS"; payload: StoredSession }
  | { type: "AUTH_FAILURE"; payload: string }
  | { type: "LOGOUT" }
  | { type: "REPLACE_USER"; payload: AuthUser }
  | { type: "CLEAR_ERROR" };

const INITIAL_STATE: AuthState = {
  status: "bootstrapping",
  session: null,
  error: null,
};

function reducer(state: AuthState, action: Action): AuthState {
  switch (action.type) {
    case "BOOTSTRAP_DONE":
      return {
        status: action.payload ? "authenticated" : "anonymous",
        session: action.payload,
        error: null,
      };
    case "AUTH_SUCCESS":
      return {
        status: "authenticated",
        session: action.payload,
        error: null,
      };
    case "AUTH_FAILURE":
      return {
        ...state,
        error: action.payload,
      };
    case "LOGOUT":
      return {
        status: "anonymous",
        session: null,
        error: null,
      };
    case "REPLACE_USER":
      if (!state.session) {
        return state;
      }
      return {
        ...state,
        session: {
          ...state.session,
          user: action.payload,
        },
      };
    case "CLEAR_ERROR":
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
}

const AuthContext = createContext<AuthContextValue | null>(null);

function normalizeError(error: unknown) {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha ao autenticar a sessao.";
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const session = await api.bootstrapSession();
        if (cancelled) {
          return;
        }
        dispatch({
          type: "BOOTSTRAP_DONE",
          payload: session,
        });
      } catch {
        if (cancelled) {
          return;
        }
        dispatch({
          type: "BOOTSTRAP_DONE",
          payload: null,
        });
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  async function login(email: string, password: string) {
    dispatch({ type: "CLEAR_ERROR" });
    try {
      const session = await api.login(email, password);
      startTransition(() => {
        dispatch({
          type: "AUTH_SUCCESS",
          payload: session,
        });
      });
    } catch (error) {
      dispatch({
        type: "AUTH_FAILURE",
        payload: normalizeError(error),
      });
      throw error;
    }
  }

  async function logout() {
    await api.logout();
    dispatch({ type: "LOGOUT" });
  }

  function replaceSessionUser(user: AuthUser) {
    if (!state.session) {
      return;
    }
    const nextSession = {
      ...state.session,
      user,
    };
    api.persistSession(nextSession);
    dispatch({
      type: "REPLACE_USER",
      payload: user,
    });
  }

  const value = useMemo<AuthContextValue>(
    () => ({
      status: state.status,
      user: state.session?.user ?? null,
      session: state.session,
      error: state.error,
      login,
      logout,
      replaceSessionUser,
      clearError: () => dispatch({ type: "CLEAR_ERROR" }),
    }),
    [state],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth precisa ser usado dentro de AuthProvider.");
  }
  return context;
}
