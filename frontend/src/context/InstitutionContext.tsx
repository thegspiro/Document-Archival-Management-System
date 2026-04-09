/** Institution context — name, logo, advisory text. */
import { createContext, useContext, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';

interface InstitutionSettings {
  name: string;
  logo_path: string | null;
  tagline: string | null;
  contact_email: string | null;
  default_advisory_text: string | null;
}

const defaults: InstitutionSettings = {
  name: 'ADMS Archive',
  logo_path: null,
  tagline: null,
  contact_email: null,
  default_advisory_text: null,
};

const InstitutionContext = createContext<InstitutionSettings>(defaults);

export function InstitutionProvider({ children }: { children: ReactNode }) {
  const { data } = useQuery({
    queryKey: ['institution-settings'],
    queryFn: async () => {
      const res = await apiClient.get('/public/institution');
      return res.data as InstitutionSettings;
    },
    staleTime: 60 * 60 * 1000,
    retry: false,
  });

  return (
    <InstitutionContext.Provider value={data || defaults}>
      {children}
    </InstitutionContext.Provider>
  );
}

export function useInstitution() {
  return useContext(InstitutionContext);
}
