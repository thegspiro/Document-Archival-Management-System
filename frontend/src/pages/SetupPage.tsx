/**
 * First-run setup wizard for creating the initial superadmin account,
 * configuring institution name, storage scheme, and optional LLM settings.
 * Redirects to /dashboard when setup is complete.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import apiClient from '../api/client';

const TOTAL_STEPS = 4;

const accountSchema = z
  .object({
    email: z.string().min(1, 'Email is required').email('Enter a valid email'),
    display_name: z.string().min(1, 'Display name is required'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    password_confirm: z.string().min(1, 'Confirm your password'),
  })
  .refine((d) => d.password === d.password_confirm, {
    message: 'Passwords do not match',
    path: ['password_confirm'],
  });

const institutionSchema = z.object({
  institution_name: z.string().min(1, 'Institution name is required'),
  institution_tagline: z.string().optional(),
});

const storageSchema = z.object({
  storage_scheme: z.enum(['date', 'location', 'donor', 'subject', 'record_number']),
  accession_format: z.string().min(1, 'Accession format is required'),
});

const llmSchema = z.object({
  llm_provider: z.enum(['none', 'openai', 'anthropic', 'ollama']),
  llm_api_key: z.string().optional(),
  llm_base_url: z.string().optional(),
  llm_model: z.string().optional(),
});

type AccountData = z.infer<typeof accountSchema>;
type InstitutionData = z.infer<typeof institutionSchema>;
type StorageData = z.infer<typeof storageSchema>;
type LlmData = z.infer<typeof llmSchema>;

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <nav aria-label="Setup progress" className="mb-8">
      <ol className="flex items-center gap-2">
        {Array.from({ length: total }, (_, i) => {
          const step = i + 1;
          const isActive = step === current;
          const isComplete = step < current;
          return (
            <li key={step} className="flex items-center gap-2">
              <span
                className={`w-8 h-8 flex items-center justify-center rounded-full text-sm font-medium ${
                  isActive
                    ? 'bg-blue-700 text-white'
                    : isComplete
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                }`}
                aria-current={isActive ? 'step' : undefined}
              >
                {isComplete ? '\u2713' : step}
              </span>
              {step < total && (
                <span className="w-8 h-px bg-gray-300 dark:bg-gray-600" aria-hidden="true" />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export default function SetupPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [institutionData, setInstitutionData] = useState<InstitutionData | null>(null);
  const [storageData, setStorageData] = useState<StorageData | null>(null);

  const accountForm = useForm<AccountData>({
    resolver: zodResolver(accountSchema),
    defaultValues: { email: '', display_name: '', password: '', password_confirm: '' },
  });

  const institutionForm = useForm<InstitutionData>({
    resolver: zodResolver(institutionSchema),
    defaultValues: { institution_name: '', institution_tagline: '' },
  });

  const storageForm = useForm<StorageData>({
    resolver: zodResolver(storageSchema),
    defaultValues: { storage_scheme: 'date', accession_format: '{YEAR}-{SEQUENCE:04d}' },
  });

  const llmForm = useForm<LlmData>({
    resolver: zodResolver(llmSchema),
    defaultValues: { llm_provider: 'none', llm_api_key: '', llm_base_url: '', llm_model: '' },
  });

  const handleAccountSubmit = (data: AccountData) => {
    setAccountData(data);
    setStep(2);
  };

  const handleInstitutionSubmit = (data: InstitutionData) => {
    setInstitutionData(data);
    setStep(3);
  };

  const handleStorageSubmit = (data: StorageData) => {
    setStorageData(data);
    setStep(4);
  };

  const handleFinalSubmit = async (llm: LlmData) => {
    if (!accountData || !institutionData || !storageData) return;
    setServerError(null);
    setIsSubmitting(true);
    try {
      await apiClient.post('/setup', {
        account: {
          email: accountData.email,
          display_name: accountData.display_name,
          password: accountData.password,
        },
        institution: institutionData,
        storage: storageData,
        llm: llm.llm_provider !== 'none' ? llm : { llm_provider: 'none' },
      });
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Setup failed. Please try again.';
      setServerError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputClasses =
    'w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2';

  const labelClasses = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

  const buttonClasses =
    'min-h-[44px] rounded bg-blue-700 hover:bg-blue-800 text-white font-medium py-2 px-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2 disabled:opacity-60';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4 py-12">
      <main className="w-full max-w-lg bg-white dark:bg-gray-800 rounded-lg shadow-md p-8" role="main">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          ADMS Setup
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
          Step {step} of {TOTAL_STEPS}
        </p>

        <StepIndicator current={step} total={TOTAL_STEPS} />

        {serverError && (
          <div
            role="alert"
            className="mb-4 p-3 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 text-sm"
          >
            {serverError}
          </div>
        )}

        {/* Step 1: Superadmin Account */}
        {step === 1 && (
          <form onSubmit={accountForm.handleSubmit(handleAccountSubmit)} noValidate>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Create Superadmin Account
            </h2>

            <div className="mb-4">
              <label htmlFor="setup-email" className={labelClasses}>
                Email <span aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                id="setup-email"
                type="email"
                autoComplete="email"
                aria-required="true"
                aria-invalid={accountForm.formState.errors.email ? 'true' : undefined}
                aria-describedby={accountForm.formState.errors.email ? 'setup-email-err' : undefined}
                className={inputClasses}
                {...accountForm.register('email')}
              />
              {accountForm.formState.errors.email && (
                <p id="setup-email-err" className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {accountForm.formState.errors.email.message}
                </p>
              )}
            </div>

            <div className="mb-4">
              <label htmlFor="setup-name" className={labelClasses}>
                Display name <span aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                id="setup-name"
                type="text"
                autoComplete="name"
                aria-required="true"
                aria-invalid={accountForm.formState.errors.display_name ? 'true' : undefined}
                aria-describedby={accountForm.formState.errors.display_name ? 'setup-name-err' : undefined}
                className={inputClasses}
                {...accountForm.register('display_name')}
              />
              {accountForm.formState.errors.display_name && (
                <p id="setup-name-err" className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {accountForm.formState.errors.display_name.message}
                </p>
              )}
            </div>

            <div className="mb-4">
              <label htmlFor="setup-password" className={labelClasses}>
                Password <span aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                id="setup-password"
                type="password"
                autoComplete="new-password"
                aria-required="true"
                aria-invalid={accountForm.formState.errors.password ? 'true' : undefined}
                aria-describedby={accountForm.formState.errors.password ? 'setup-pw-err' : undefined}
                className={inputClasses}
                {...accountForm.register('password')}
              />
              {accountForm.formState.errors.password && (
                <p id="setup-pw-err" className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {accountForm.formState.errors.password.message}
                </p>
              )}
            </div>

            <div className="mb-6">
              <label htmlFor="setup-password-confirm" className={labelClasses}>
                Confirm password <span aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                id="setup-password-confirm"
                type="password"
                autoComplete="new-password"
                aria-required="true"
                aria-invalid={accountForm.formState.errors.password_confirm ? 'true' : undefined}
                aria-describedby={
                  accountForm.formState.errors.password_confirm ? 'setup-pwc-err' : undefined
                }
                className={inputClasses}
                {...accountForm.register('password_confirm')}
              />
              {accountForm.formState.errors.password_confirm && (
                <p id="setup-pwc-err" className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {accountForm.formState.errors.password_confirm.message}
                </p>
              )}
            </div>

            <button type="submit" className={buttonClasses}>
              Next
            </button>
          </form>
        )}

        {/* Step 2: Institution */}
        {step === 2 && (
          <form onSubmit={institutionForm.handleSubmit(handleInstitutionSubmit)} noValidate>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Institution Information
            </h2>

            <div className="mb-4">
              <label htmlFor="setup-inst-name" className={labelClasses}>
                Institution name <span aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                id="setup-inst-name"
                type="text"
                aria-required="true"
                aria-invalid={institutionForm.formState.errors.institution_name ? 'true' : undefined}
                aria-describedby={
                  institutionForm.formState.errors.institution_name ? 'setup-inst-err' : undefined
                }
                className={inputClasses}
                {...institutionForm.register('institution_name')}
              />
              {institutionForm.formState.errors.institution_name && (
                <p id="setup-inst-err" className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {institutionForm.formState.errors.institution_name.message}
                </p>
              )}
            </div>

            <div className="mb-6">
              <label htmlFor="setup-inst-tagline" className={labelClasses}>
                Tagline (optional)
              </label>
              <input
                id="setup-inst-tagline"
                type="text"
                className={inputClasses}
                {...institutionForm.register('institution_tagline')}
              />
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium py-2 px-6 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
              >
                Back
              </button>
              <button type="submit" className={buttonClasses}>
                Next
              </button>
            </div>
          </form>
        )}

        {/* Step 3: Storage Scheme */}
        {step === 3 && (
          <form onSubmit={storageForm.handleSubmit(handleStorageSubmit)} noValidate>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Storage Configuration
            </h2>

            <fieldset className="mb-4">
              <legend className={labelClasses}>
                Storage scheme <span aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </legend>
              <div className="space-y-2 mt-1">
                {[
                  { value: 'date', label: 'By date (year/month)' },
                  { value: 'location', label: 'By archival location (fonds/series)' },
                  { value: 'donor', label: 'By donor' },
                  { value: 'subject', label: 'By subject category' },
                  { value: 'record_number', label: 'By record number' },
                ].map((opt) => (
                  <label key={opt.value} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input
                      type="radio"
                      value={opt.value}
                      className="h-4 w-4"
                      {...storageForm.register('storage_scheme')}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="mb-6">
              <label htmlFor="setup-accession-fmt" className={labelClasses}>
                Accession number format <span aria-hidden="true">*</span>
                <span className="sr-only">(required)</span>
              </label>
              <input
                id="setup-accession-fmt"
                type="text"
                aria-required="true"
                aria-describedby="setup-accession-hint"
                className={inputClasses}
                {...storageForm.register('accession_format')}
              />
              <p id="setup-accession-hint" className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Use tokens: {'{YEAR}'}, {'{MONTH}'}, {'{DAY}'}, {'{SEQUENCE:04d}'}. Default: {'{YEAR}-{SEQUENCE:04d}'}
              </p>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium py-2 px-6 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
              >
                Back
              </button>
              <button type="submit" className={buttonClasses}>
                Next
              </button>
            </div>
          </form>
        )}

        {/* Step 4: LLM (optional) */}
        {step === 4 && (
          <form onSubmit={llmForm.handleSubmit(handleFinalSubmit)} noValidate>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              LLM Configuration (Optional)
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Configure an LLM provider for metadata suggestions. You can skip this and configure it later.
            </p>

            <div className="mb-4">
              <label htmlFor="setup-llm-provider" className={labelClasses}>
                Provider
              </label>
              <select
                id="setup-llm-provider"
                className={inputClasses}
                {...llmForm.register('llm_provider')}
              >
                <option value="none">None (skip)</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>

            {llmForm.watch('llm_provider') !== 'none' && (
              <>
                <div className="mb-4">
                  <label htmlFor="setup-llm-key" className={labelClasses}>
                    API key
                  </label>
                  <input
                    id="setup-llm-key"
                    type="password"
                    autoComplete="off"
                    className={inputClasses}
                    {...llmForm.register('llm_api_key')}
                  />
                </div>

                {llmForm.watch('llm_provider') === 'ollama' && (
                  <div className="mb-4">
                    <label htmlFor="setup-llm-url" className={labelClasses}>
                      Base URL
                    </label>
                    <input
                      id="setup-llm-url"
                      type="url"
                      placeholder="http://localhost:11434"
                      className={inputClasses}
                      {...llmForm.register('llm_base_url')}
                    />
                  </div>
                )}

                <div className="mb-6">
                  <label htmlFor="setup-llm-model" className={labelClasses}>
                    Model
                  </label>
                  <input
                    id="setup-llm-model"
                    type="text"
                    className={inputClasses}
                    {...llmForm.register('llm_model')}
                  />
                </div>
              </>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(3)}
                className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium py-2 px-6 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
              >
                Back
              </button>
              <button type="submit" disabled={isSubmitting} className={buttonClasses}>
                {isSubmitting ? 'Completing setup...' : 'Complete Setup'}
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}
