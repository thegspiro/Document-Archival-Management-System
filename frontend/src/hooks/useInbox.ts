/** Inbox count hook — polls periodically for badge update. */
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useInboxStore } from '../stores/inbox';

export function useInbox() {
  const { count, setCount } = useInboxStore();

  const { data } = useQuery({
    queryKey: ['inbox-count'],
    queryFn: async () => {
      const res = await apiClient.get('/documents', {
        params: { inbox_status: 'inbox', per_page: 1 },
      });
      return res.data.total as number;
    },
    refetchInterval: 30000,
  });

  useEffect(() => {
    if (data !== undefined) {
      setCount(data);
    }
  }, [data, setCount]);

  return count;
}
