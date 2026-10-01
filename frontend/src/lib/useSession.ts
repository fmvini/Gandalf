import { useSyncExternalStore } from 'react'
import { authSession } from './auth'

export function useSession() {
  return useSyncExternalStore(authSession.subscribe, authSession.getSnapshot)
}
