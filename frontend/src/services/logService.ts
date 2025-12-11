import { apiService } from './api';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  category: string;
  message: string;
  metadata?: Record<string, any>;
  source?: string;
}

export interface LogStats {
  total: number;
  byLevel: Record<string, number>;
  byCategory: Record<string, number>;
  timeRange: {
    start: string;
    end: string;
  };
}

export interface LogFilter {
  level?: string[];
  category?: string[];
  startDate?: string;
  endDate?: string;
  limit?: number;
  offset?: number;
}

class LogService {
  async getLogs(filter?: LogFilter): Promise<LogEntry[]> {
    const queryParams = new URLSearchParams();
    if (filter) {
      if (filter.level) queryParams.append('level', filter.level.join(','));
      if (filter.category) queryParams.append('category', filter.category.join(','));
      if (filter.startDate) queryParams.append('startDate', filter.startDate);
      if (filter.endDate) queryParams.append('endDate', filter.endDate);
      if (filter.limit) queryParams.append('limit', filter.limit.toString());
      if (filter.offset) queryParams.append('offset', filter.offset.toString());
    }
    const endpoint = `/logs${queryParams.toString() ? `?${queryParams}` : ''}`;
    return apiService.get<LogEntry[]>(endpoint);
  }

  async getLog(logId: string): Promise<LogEntry> {
    return apiService.get<LogEntry>(`/logs/${logId}`);
  }

  async getStats(filter?: { startDate?: string; endDate?: string }): Promise<LogStats> {
    const queryParams = new URLSearchParams();
    if (filter?.startDate) queryParams.append('startDate', filter.startDate);
    if (filter?.endDate) queryParams.append('endDate', filter.endDate);
    const endpoint = `/logs/stats${queryParams.toString() ? `?${queryParams}` : ''}`;
    return apiService.get<LogStats>(endpoint);
  }

  async clearLogs(level?: string): Promise<void> {
    const endpoint = level ? `/logs/clear?level=${level}` : '/logs/clear';
    return apiService.post(endpoint, {});
  }

  async exportLogs(filter?: LogFilter): Promise<Blob> {
    const queryParams = new URLSearchParams();
    if (filter) {
      if (filter.level) queryParams.append('level', filter.level.join(','));
      if (filter.category) queryParams.append('category', filter.category.join(','));
      if (filter.startDate) queryParams.append('startDate', filter.startDate);
      if (filter.endDate) queryParams.append('endDate', filter.endDate);
    }
    const endpoint = `/logs/export${queryParams.toString() ? `?${queryParams}` : ''}`;
    const response = await fetch(`${apiService['baseUrl']}${endpoint}`);
    return response.blob();
  }
}

export const logService = new LogService();
export default logService;
