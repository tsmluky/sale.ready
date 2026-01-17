
import React, { useState, useEffect } from 'react';
import { Bell, CheckCircle, AlertTriangle, Info, BellRing } from 'lucide-react';
import { Notification as AppNotification } from '../types';
import { API_BASE_URL } from '../constants';
import { api } from '../services/api';

// Helper to convert VAPID key
function urlBase64ToUint8Array(base64String: string) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const NotificationCenter: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [pushStatus, setPushStatus] = useState<'default' | 'granted' | 'denied' | 'unsupported'>('default');
  const [subscribing, setSubscribing] = useState(false);

  useEffect(() => {
    // 1. Initial Check for Push Support
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      setPushStatus('unsupported');
    } else if (Notification.permission === 'granted') {
      setPushStatus('granted');
    } else if (Notification.permission === 'denied') {
      setPushStatus('denied');
    }

    // 2. Fetch Recent Signals as Notifications
    const fetchNotifications = async () => {
      try {
        // We use logs as the source of truth for "notifications" for now
        const data = await api.get('/logs/recent?limit=10');
        if (data) {
          const mapped: AppNotification[] = data.map((log: any) => ({
            id: log.id.toString(),
            title: `${log.direction} ${log.token}`,
            message: `Entry: ${log.entry} | Source: ${log.source}`,
            time: new Date(log.timestamp).toLocaleTimeString(),
            type: log.status === 'WIN' ? 'success' : log.status === 'LOSS' ? 'alert' : 'info',
            read: false // Default to false for new items
          }));

          setNotifications(prev => {
            const existingMap = new Map(prev.map(n => [n.id, n]));
            return mapped.map(newNotif => {
              const existing = existingMap.get(newNotif.id);
              return existing ? { ...newNotif, read: existing.read } : newNotif;
            });
          });
        }
      } catch (e) {
        console.error("Failed to fetch notifications", e);
      }
    };

    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000); // Poll every 15s
    return () => clearInterval(interval);

  }, []);

  const enablePush = async () => {
    if (pushStatus === 'unsupported') return;
    setSubscribing(true);

    try {
      // 1. Request Permission
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        setPushStatus('denied');
        setSubscribing(false);
        return;
      }

      setPushStatus('granted');

      // 2. Register SW (ensure it is registered)
      // Note: SW is usually registered in main.tsx or index.html, but let's ensure it.
      const registration = await navigator.serviceWorker.register('/sw.js');
      await navigator.serviceWorker.ready;

      // 3. Subscribe
      const vapidKey = import.meta.env.VITE_VAPID_PUBLIC_KEY;
      if (!vapidKey) {
        console.error("Missing VAPID Key");
        return;
      }

      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey)
      });

      // 4. Send to Backend
      await fetch(`${API_BASE_URL}/notifications/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription)
      });

      // Add notification
      setNotifications(prev => [{
        id: Date.now().toString(),
        title: 'Notifications Enabled',
        message: 'You will now receive alerts for new signals.',
        time: 'Just now',
        type: 'success',
        read: false
      }, ...prev]);

    } catch (error) {
      console.error("Push Error:", error);
      // alert("Failed to enable notifications.");
    } finally {
      setSubscribing(false);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  return (
    <div className="relative z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-full hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        title="Notifications"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-rose-500 rounded-full border-2 border-slate-900"></span>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)}></div>
          <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2">
            <div className="p-3 border-b border-slate-800 flex justify-between items-center bg-slate-900/95 backdrop-blur">
              <h3 className="text-sm font-bold text-white">Notifications</h3>
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="text-[10px] text-emerald-400 hover:text-emerald-300 font-bold uppercase">
                  Mark all read
                </button>
              )}
            </div>

            {/* Push Enable Banner */}
            {pushStatus === 'default' && (
              <div className="p-3 bg-indigo-500/10 border-b border-indigo-500/20">
                <div className="flex items-start gap-3">
                  <BellRing size={16} className="text-indigo-400 mt-1" />
                  <div>
                    <p className="text-xs text-indigo-300 font-medium mb-2">
                      Get real-time signal alerts even when you're away.
                    </p>
                    <button
                      onClick={enablePush}
                      disabled={subscribing}
                      className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-md font-medium transition-colors w-full"
                    >
                      {subscribing ? 'Enabling...' : 'Enable Signal Alerts'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="max-h-[300px] overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs">No notifications</div>
              ) : (
                notifications.map(n => (
                  <div key={n.id} className={`p-4 border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors ${n.read ? 'opacity-60' : 'opacity-100'}`}>
                    <div className="flex gap-3">
                      <div className="mt-0.5">
                        {n.type === 'success' && <CheckCircle size={14} className="text-emerald-400" />}
                        {n.type === 'alert' && <AlertTriangle size={14} className="text-amber-400" />}
                        {n.type === 'info' && <Info size={14} className="text-blue-400" />}
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start">
                          <h4 className="text-sm font-bold text-slate-200">{n.title}</h4>
                          <span className="text-[10px] text-slate-500">{n.time}</span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{n.message}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
