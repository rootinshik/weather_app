import {
  createContext, useContext, useState, useEffect, useCallback, type ReactNode,
} from 'react';
import { getCookie, setCookie } from '../utils/cookies';
import { apiClient } from '../api/client';
import type { UserResponse } from '../types/user';

const COOKIE_NAME = 'weather_uid';
const COOKIE_MAX_DAYS = 180;

interface UserContextValue {
  externalId: string;
  userId: number | null;
  user: UserResponse | null;
  identify: () => Promise<void>;
}

const UserContext = createContext<UserContextValue | null>(null);

function getOrCreateExternalId(): string {
  let uid = getCookie(COOKIE_NAME);
  if (!uid) {
    uid = crypto.randomUUID();
    setCookie(COOKIE_NAME, uid, COOKIE_MAX_DAYS);
  }
  return uid;
}

export function UserProvider({ children }: { children: ReactNode }) {
  const [externalId] = useState<string>(getOrCreateExternalId);
  const [user, setUser] = useState<UserResponse | null>(null);

  const identify = useCallback(async () => {
    const result = await apiClient.post<UserResponse>('/users/identify', {
      platform: 'web',
      external_id: externalId,
    });
    setUser(result);
  }, [externalId]);

  useEffect(() => {
    identify().catch(() => {
      // Backend may be unavailable; user will be identified on next interaction
    });
  }, [identify]);

  return (
    <UserContext.Provider
      value={{ externalId, userId: user?.id ?? null, user, identify }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUser must be used within UserProvider');
  return ctx;
}
