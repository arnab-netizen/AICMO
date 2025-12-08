/**
 * CAM Phase 9: Safety & Limits Panel
 * 
 * UI for managing rate limits, warmup settings, send windows, and DNC lists.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Save, Shield, Clock, Ban } from 'lucide-react';

interface ChannelLimitConfig {
  channel: string;
  max_per_day: number;
  warmup_enabled: boolean;
  warmup_start?: number;
  warmup_increment?: number;
  warmup_max?: number;
}

interface SafetySettings {
  per_channel_limits: Record<string, ChannelLimitConfig>;
  send_window_start?: string;
  send_window_end?: string;
  blocked_domains: string[];
  do_not_contact_emails: string[];
  do_not_contact_lead_ids: number[];
}

export default function CamSafetyPanel() {
  const [settings, setSettings] = useState<SafetySettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/cam/safety');
      
      if (!response.ok) {
        throw new Error(`Failed to load settings: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load safety settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!settings) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const response = await fetch('/api/cam/safety', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error(`Failed to save settings: ${response.statusText}`);
      }

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save safety settings');
    } finally {
      setSaving(false);
    }
  };

  const updateChannelLimit = (channel: string, field: keyof ChannelLimitConfig, value: any) => {
    if (!settings) return;

    setSettings({
      ...settings,
      per_channel_limits: {
        ...settings.per_channel_limits,
        [channel]: {
          ...settings.per_channel_limits[channel],
          [field]: value,
        },
      },
    });
  };

  const updateBlockedDomains = (value: string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      blocked_domains: value.split('\n').map(d => d.trim()).filter(d => d),
    });
  };

  const updateDncEmails = (value: string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      do_not_contact_emails: value.split('\n').map(e => e.trim()).filter(e => e),
    });
  };

  const updateDncLeadIds = (value: string) => {
    if (!settings) return;
    const ids = value.split('\n')
      .map(id => parseInt(id.trim()))
      .filter(id => !isNaN(id));
    setSettings({
      ...settings,
      do_not_contact_lead_ids: ids,
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!settings) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Failed to load safety settings. Please try again.</AlertDescription>
      </Alert>
    );
  }

  const channels = ['email', 'linkedin', 'twitter'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Safety & Limits</h2>
          <p className="text-sm text-gray-600">
            Configure rate limits, send windows, and contact restrictions
          </p>
        </div>
        <Button onClick={saveSettings} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <Alert className="bg-green-50 border-green-200">
          <AlertDescription className="text-green-800">
            Safety settings saved successfully!
          </AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Rate Limits Per Channel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="mr-2 h-5 w-5" />
            Rate Limits by Channel
          </CardTitle>
          <CardDescription>
            Set daily message limits with optional warmup periods for each channel
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {channels.map(channel => {
            const config = settings.per_channel_limits[channel];
            if (!config) return null;

            return (
              <div key={channel} className="border rounded-lg p-4 space-y-4">
                <h4 className="font-semibold capitalize">{channel}</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor={`${channel}-max`}>Max Per Day</Label>
                    <Input
                      id={`${channel}-max`}
                      type="number"
                      value={config.max_per_day}
                      onChange={(e) => updateChannelLimit(channel, 'max_per_day', parseInt(e.target.value))}
                      min={1}
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id={`${channel}-warmup`}
                    checked={config.warmup_enabled}
                    onCheckedChange={(checked) => updateChannelLimit(channel, 'warmup_enabled', checked)}
                  />
                  <Label htmlFor={`${channel}-warmup`} className="cursor-pointer">
                    Enable Warmup (gradually increase daily limit)
                  </Label>
                </div>

                {config.warmup_enabled && (
                  <div className="grid grid-cols-3 gap-4 pl-6">
                    <div>
                      <Label htmlFor={`${channel}-warmup-start`}>Start (Day 1)</Label>
                      <Input
                        id={`${channel}-warmup-start`}
                        type="number"
                        value={config.warmup_start || ''}
                        onChange={(e) => updateChannelLimit(channel, 'warmup_start', parseInt(e.target.value) || null)}
                        placeholder="e.g., 5"
                        min={1}
                      />
                    </div>
                    <div>
                      <Label htmlFor={`${channel}-warmup-inc`}>Daily Increment</Label>
                      <Input
                        id={`${channel}-warmup-inc`}
                        type="number"
                        value={config.warmup_increment || ''}
                        onChange={(e) => updateChannelLimit(channel, 'warmup_increment', parseInt(e.target.value) || null)}
                        placeholder="e.g., 2"
                        min={1}
                      />
                    </div>
                    <div>
                      <Label htmlFor={`${channel}-warmup-max`}>Max Limit</Label>
                      <Input
                        id={`${channel}-warmup-max`}
                        type="number"
                        value={config.warmup_max || ''}
                        onChange={(e) => updateChannelLimit(channel, 'warmup_max', parseInt(e.target.value) || null)}
                        placeholder="e.g., 20"
                        min={1}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Send Window */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Clock className="mr-2 h-5 w-5" />
            Send Window
          </CardTitle>
          <CardDescription>
            Restrict outreach to specific hours (leave empty for 24/7 sending)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="window-start">Start Time (HH:MM)</Label>
              <Input
                id="window-start"
                type="time"
                value={settings.send_window_start || ''}
                onChange={(e) => setSettings({ ...settings, send_window_start: e.target.value || undefined })}
                placeholder="09:00"
              />
            </div>
            <div>
              <Label htmlFor="window-end">End Time (HH:MM)</Label>
              <Input
                id="window-end"
                type="time"
                value={settings.send_window_end || ''}
                onChange={(e) => setSettings({ ...settings, send_window_end: e.target.value || undefined })}
                placeholder="18:00"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Do Not Contact Lists */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Ban className="mr-2 h-5 w-5" />
            Do Not Contact Lists
          </CardTitle>
          <CardDescription>
            Block specific contacts, domains, or lead IDs from receiving outreach
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="dnc-emails">Blocked Email Addresses (one per line)</Label>
            <Textarea
              id="dnc-emails"
              value={settings.do_not_contact_emails.join('\n')}
              onChange={(e) => updateDncEmails(e.target.value)}
              placeholder="example@domain.com&#10;blocked@company.com"
              rows={5}
            />
          </div>

          <div>
            <Label htmlFor="blocked-domains">Blocked Domains (one per line)</Label>
            <Textarea
              id="blocked-domains"
              value={settings.blocked_domains.join('\n')}
              onChange={(e) => updateBlockedDomains(e.target.value)}
              placeholder="competitor.com&#10;unsubscribed.com"
              rows={5}
            />
          </div>

          <div>
            <Label htmlFor="dnc-lead-ids">Blocked Lead IDs (one per line)</Label>
            <Textarea
              id="dnc-lead-ids"
              value={settings.do_not_contact_lead_ids.join('\n')}
              onChange={(e) => updateDncLeadIds(e.target.value)}
              placeholder="123&#10;456"
              rows={5}
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button (bottom) */}
      <div className="flex justify-end">
        <Button onClick={saveSettings} disabled={saving} size="lg">
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
