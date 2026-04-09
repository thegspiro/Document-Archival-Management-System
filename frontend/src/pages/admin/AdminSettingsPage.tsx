/**
 * System settings page. Manages institution config, LLM settings,
 * storage scheme, accession format, and fixity schedule.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';

interface SystemSettings {
  [key: string]: unknown;
}

export default function AdminSettingsPage() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading, isError } = useQuery<SystemSettings>({
    queryKey: ['admin', 'settings'],
    queryFn: () => apiClient.get('/settings').then((r) => r.data),
  });

  const [form, setForm] = useState<Record<string, string>>({});
  const [saveMsg, setSaveMsg] = useState('');

  useEffect(() => {
    if (settings) {
      const flat: Record<string, string> = {};
      for (const [key, val] of Object.entries(settings)) {
        flat[key] = typeof val === 'string' ? val : JSON.stringify(val);
      }
      setForm(flat);
    }
  }, [settings]);

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => apiClient.patch('/settings', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'settings'] });
      setSaveMsg('Settings saved successfully.');
      setTimeout(() => setSaveMsg(''), 3000);
    },
    onError: () => setSaveMsg('Failed to save settings.'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(form);
  };

  if (isLoading) return <div className="flex items-center justify-center py-16"><Spinner label="Loading settings" /></div>;

  if (isError) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load system settings.</div>
      </div>
    );
  }

  const settingGroups = [
    { label: 'Institution', keys: ['institution.name', 'institution.naan', 'institution.contact_email'] },
    { label: 'LLM Configuration', keys: ['llm.provider', 'llm.enabled_suggestion_fields', 'llm.require_review', 'llm.auto_apply_threshold'] },
    { label: 'NER Configuration', keys: ['ner.enabled', 'ner.run_after_ocr', 'ner.model', 'ner.require_review'] },
    { label: 'Fixity Schedule', keys: ['fixity.schedule_cron'] },
    { label: 'Content Advisory', keys: ['content_advisory.default_text'] },
  ];

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">System Settings</h1>

      {saveMsg && (
        <div role="status" aria-live="polite" className={`mb-4 p-3 rounded text-sm ${saveMsg.includes('Failed') ? 'bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200' : 'bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200'}`}>
          {saveMsg}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {settingGroups.map((group) => (
          <fieldset key={group.label} className="mb-8">
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">{group.label}</legend>
            <div className="space-y-4">
              {group.keys.map((key) => (
                <div key={key}>
                  <label htmlFor={`setting-${key}`} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {key}
                  </label>
                  <input id={`setting-${key}`} type="text" value={form[key] ?? ''}
                    onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))}
                    className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
                </div>
              ))}
            </div>
          </fieldset>
        ))}

        <button type="submit" disabled={mutation.isPending}
          className="min-h-[44px] px-6 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          {mutation.isPending ? 'Saving...' : 'Save Settings'}
        </button>
      </form>
    </div>
  );
}
