import { apiService } from './api';

export interface Plugin {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  isEnabled: boolean;
  isInstalled: boolean;
  category: string;
  config?: Record<string, any>;
  capabilities: string[];
}

export interface PluginStats {
  pluginId: string;
  totalCalls: number;
  successRate: number;
  avgExecutionTime: number;
  lastUsed: string;
}

class PluginService {
  async getPlugins(): Promise<Plugin[]> {
    return apiService.get<Plugin[]>('/plugins');
  }

  async getPlugin(pluginId: string): Promise<Plugin> {
    return apiService.get<Plugin>(`/plugins/${pluginId}`);
  }

  async installPlugin(pluginId: string): Promise<Plugin> {
    return apiService.post<Plugin>(`/plugins/${pluginId}/install`, {});
  }

  async uninstallPlugin(pluginId: string): Promise<void> {
    return apiService.post(`/plugins/${pluginId}/uninstall`, {});
  }

  async enablePlugin(pluginId: string): Promise<Plugin> {
    return apiService.post<Plugin>(`/plugins/${pluginId}/enable`, {});
  }

  async disablePlugin(pluginId: string): Promise<Plugin> {
    return apiService.post<Plugin>(`/plugins/${pluginId}/disable`, {});
  }

  async updatePluginConfig(pluginId: string, config: Record<string, any>): Promise<Plugin> {
    return apiService.put<Plugin>(`/plugins/${pluginId}/config`, { config });
  }

  async getPluginStats(pluginId: string): Promise<PluginStats> {
    return apiService.get<PluginStats>(`/plugins/${pluginId}/stats`);
  }

  async getAvailablePlugins(): Promise<Plugin[]> {
    return apiService.get<Plugin[]>('/plugins/available');
  }
}

export const pluginService = new PluginService();
export default pluginService;
