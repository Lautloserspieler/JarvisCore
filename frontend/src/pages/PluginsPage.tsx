import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import PluginsTab from '@/components/tabs/PluginsTab';

const PluginsPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-4 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">{t('tabs.plugins') || 'Plugins'}</h1>
            <p className="text-sm text-muted-foreground">
              {t('pluginsTab.subtitle') || 'Status, API-Keys und Aktivierung verwalten'}
            </p>
          </div>
          <Button variant="outline" asChild>
            <Link to="/">{t('navigation.back') || 'Zurück'}</Link>
          </Button>
        </div>

        <Card className="holo-panel">
          <CardHeader>
            <CardTitle>{t('tabs.plugins') || 'Plugins'}</CardTitle>
            <CardDescription>
              {t('pluginsTab.healthDescription') || 'Überwache den Zustand der Plugins und aktiviere sie bei Bedarf.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PluginsTab />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PluginsPage;
