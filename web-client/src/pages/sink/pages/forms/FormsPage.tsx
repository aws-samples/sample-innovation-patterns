import { AppearanceSettings } from '@/pages/sink/pages/forms/appearance-settings'
import { ChatSettings } from '@/pages/sink/pages/forms/chat-settings'
import { DisplaySettings } from '@/pages/sink/pages/forms/display-settings'
import { NotionPromptForm } from '@/pages/sink/pages/forms/notion-prompt-form'
import { ShipRegistrationForm } from '@/pages/sink/pages/forms/ship-registration-form'
import { ShippingForm } from '@/pages/sink/pages/forms/shipping-form'

export function FormsPage() {
  return (
    <div className="@container flex flex-1 flex-col gap-12 p-4">
      <div className="grid flex-1 gap-12 @3xl:grid-cols-2 @5xl:grid-cols-3 @[120rem]:grid-cols-4 [&>div]:max-w-lg">
        <div className="flex flex-col gap-12">
          <NotionPromptForm />
          <ChatSettings />
        </div>
        <div className="flex flex-col gap-12">
          <AppearanceSettings />
        </div>
        <div className="flex flex-col gap-12">
          <DisplaySettings />
        </div>
        <div className="flex flex-col gap-12">
          <ShippingForm />
        </div>
        <div className="col-span-2 flex flex-col gap-12">
          <ShipRegistrationForm />
        </div>
      </div>
    </div>
  )
}
