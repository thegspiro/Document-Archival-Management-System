export default function AdminSettingsPage() {
  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">System Settings</h1>

      <div className="space-y-6">
        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Institution</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="inst-name" className="block text-sm font-medium text-gray-700 mb-1">
                Institution Name <span className="text-red-500" aria-hidden="true">*</span>
              </label>
              <input id="inst-name" type="text" className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" aria-required="true" />
            </div>
            <div>
              <label htmlFor="base-url" className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
              <input id="base-url" type="url" className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </section>

        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">LLM Configuration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="llm-provider" className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
              <select id="llm-provider" className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="none">None</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>
            <div>
              <label htmlFor="llm-model" className="block text-sm font-medium text-gray-700 mb-1">Model</label>
              <input id="llm-model" type="text" className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
        </section>

        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Accession Number Format</h2>
          <div>
            <label htmlFor="accession-format" className="block text-sm font-medium text-gray-700 mb-1">Format Template</label>
            <input id="accession-format" type="text" defaultValue="{YEAR}-{SEQUENCE:04d}" className="w-full max-w-md rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <p className="mt-1 text-sm text-gray-500">Tokens: {'{YEAR}'}, {'{MONTH}'}, {'{DAY}'}, {'{SEQUENCE}'}</p>
          </div>
        </section>

        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Fixity Check Schedule</h2>
          <div>
            <label htmlFor="fixity-cron" className="block text-sm font-medium text-gray-700 mb-1">Cron Expression</label>
            <input id="fixity-cron" type="text" defaultValue="0 2 * * 0" className="w-full max-w-md rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <p className="mt-1 text-sm text-gray-500">Default: Weekly on Sunday at 2:00 AM</p>
          </div>
        </section>

        <div className="flex justify-end">
          <button
            type="button"
            className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
