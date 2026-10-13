import React, { useEffect, useState } from 'react';
import {
  Sun,
  Moon,
  Monitor,
  Languages,
  Thermometer,
  MessageSquare,
  Eye,
  Sparkles,
  ArrowLeft,
  Menu,
  Save,
  Check,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { getSettings, updateSettings } from '../services/api';
import type { UserSettings } from '../types';

export function SettingsPage() {
  const { settings, setSettings, theme, setTheme, setCurrentPage, toggleSidebar } = useStore();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const res = await getSettings();
      if (res.data) {
        setSettings(res.data);
        if (res.data.theme) setTheme(res.data.theme);
      }
    } catch {
      // Use defaults
    }
  };

  const handleSave = async (partial: Partial<UserSettings>) => {
    const newSettings = { ...settings, ...partial };
    setSettings(partial);
    setSaving(true);
    try {
      await updateSettings(partial);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // Settings still applied locally
    } finally {
      setSaving(false);
    }
  };

  const handleThemeChange = (t: 'light' | 'dark' | 'system') => {
    setTheme(t);
    handleSave({ theme: t });
  };

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 dark:bg-surface-900/80 backdrop-blur-sm border-b border-surface-200 dark:border-surface-800 px-4 sm:px-6 py-3.5 sm:py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Mobile menu toggle */}
            <button
              onClick={toggleSidebar}
              className="btn-ghost p-1.5 lg:hidden text-surface-600 dark:text-surface-300"
              aria-label="Open navigation menu"
            >
              <Menu size={20} />
            </button>

            <div>
              <h1 className="text-base sm:text-xl font-semibold leading-tight">Settings</h1>
              <p className="text-xs sm:text-sm text-surface-500 hidden sm:block">Customise your experience</p>
            </div>
          </div>
          {saved && (
            <span className="flex items-center gap-1.5 text-xs sm:text-sm text-emerald-600 dark:text-emerald-400 animate-fade-in">
              <Check size={16} /> Saved
            </span>
          )}
        </div>
      </div>

      <div className="p-6 max-w-2xl mx-auto space-y-8">
        <Section title="Appearance" icon={<Sun size={18} />}>
          <label className="text-sm font-medium mb-3 block">Theme</label>
          <div className="grid grid-cols-3 gap-3">
            <ThemeOption icon={<Sun size={18} />} label="Light" active={theme === 'light'} onClick={() => handleThemeChange('light')} />
            <ThemeOption icon={<Moon size={18} />} label="Dark" active={theme === 'dark'} onClick={() => handleThemeChange('dark')} />
            <ThemeOption icon={<Monitor size={18} />} label="System" active={theme === 'system'} onClick={() => handleThemeChange('system')} />
          </div>
        </Section>

        <Section title="Language" icon={<Languages size={18} />}>
          <label className="text-sm font-medium mb-2 block">Response Language</label>
          <p className="text-xs text-surface-500 mb-3">Choose the language the AI should respond in</p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { code: 'en', label: 'English', flag: '🇬🇧' },
              { code: 'hi', label: 'हिंदी', flag: '🇮🇳' },
              { code: 'hinglish', label: 'Hinglish', flag: '🇮🇳' },
            ].map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleSave({ language: lang.code })}
                className={`card p-3 text-center transition-all ${
                  settings.language === lang.code
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'hover:border-surface-300 dark:hover:border-surface-600'
                }`}
              >
                <span className="text-2xl">{lang.flag}</span>
                <p className="text-sm font-medium mt-1">{lang.label}</p>
              </button>
            ))}
          </div>
        </Section>

        <Section title="AI Settings" icon={<Sparkles size={18} />}>
          <div className="space-y-5">
            <div>
              <label className="text-sm font-medium mb-1 block flex items-center gap-2">
                <Thermometer size={14} /> Temperature: {settings.temperature.toFixed(1)}
              </label>
              <p className="text-xs text-surface-500 mb-2">Lower = more focused, Higher = more creative</p>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => handleSave({ temperature: parseFloat(e.target.value) })}
                className="w-full accent-primary-600"
              />
              <div className="flex justify-between text-[10px] text-surface-400 mt-1">
                <span>Precise (0)</span>
                <span>Balanced (0.7)</span>
                <span>Creative (2)</span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-1 block">Max Response Length</label>
              <select
                value={settings.max_tokens}
                onChange={(e) => handleSave({ max_tokens: parseInt(e.target.value) })}
                className="input-field"
              >
                <option value="512">Short (512 tokens)</option>
                <option value="1024">Medium (1024 tokens)</option>
                <option value="2048">Long (2048 tokens)</option>
                <option value="4096">Very Long (4096 tokens)</option>
              </select>
            </div>
          </div>
        </Section>

        <Section title="Display" icon={<Eye size={18} />}>
          <div className="space-y-3">
            <Toggle label="Show timestamps" checked={settings.timestamps_enabled} onChange={(v) => handleSave({ timestamps_enabled: v })} />
            <Toggle label="Show sentiment indicators" checked={settings.sentiment_enabled} onChange={(v) => handleSave({ sentiment_enabled: v })} />
            <Toggle label="Compact mode" checked={settings.compact_mode} onChange={(v) => handleSave({ compact_mode: v })} />
            <Toggle label="Auto-scroll to latest message" checked={settings.auto_scroll} onChange={(v) => handleSave({ auto_scroll: v })} />
            <Toggle label="Show follow-up suggestions" checked={settings.suggestions_enabled} onChange={(v) => handleSave({ suggestions_enabled: v })} />
          </div>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="card p-5">
      <h3 className="font-semibold text-sm flex items-center gap-2 mb-4">
        <span className="text-primary-600 dark:text-primary-400">{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

function ThemeOption({ icon, label, active, onClick }: { icon: React.ReactNode; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`card p-4 text-center transition-all ${
        active ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'hover:border-surface-300 dark:hover:border-surface-600'
      }`}
    >
      <div className={`mx-auto mb-1 ${active ? 'text-primary-600 dark:text-primary-400' : 'text-surface-500'}`}>{icon}</div>
      <p className="text-sm font-medium">{label}</p>
    </button>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center justify-between cursor-pointer group">
      <span className="text-sm text-surface-700 dark:text-surface-300">{label}</span>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
          checked ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'
        }`}
      >
        <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200 ${
          checked ? 'translate-x-5' : ''
        }`} />
      </button>
    </label>
  );
}
