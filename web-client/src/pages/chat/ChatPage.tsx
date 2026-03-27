import { Thread } from '@/components/assistant-ui/thread'
import { ThreadList } from '@/components/assistant-ui/thread-list'
import { AgentCoreRuntimeProvider } from './AgentCoreRuntimeProvider'

export function ChatPage() {
  return (
    <AgentCoreRuntimeProvider>
      <div className="flex h-[calc(100vh-3.5rem)]">
        <div className="w-64 border-r p-2">
          <ThreadList />
        </div>
        <div className="flex-1">
          <Thread />
        </div>
      </div>
    </AgentCoreRuntimeProvider>
  )
}
