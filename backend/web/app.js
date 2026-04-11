import React, { useEffect, useState } from 'https://esm.sh/react@18.3.1';
import { createRoot } from 'https://esm.sh/react-dom@18.3.1/client';
import htm from 'https://esm.sh/htm';

const html = htm.bind(React.createElement);
const API_BASE = '';

function useStoredToken() {
  const [token, setToken] = useState(() => localStorage.getItem('token') || '');
  const save = (t) => {
    setToken(t);
    if (t) localStorage.setItem('token', t);
    else localStorage.removeItem('token');
  };
  return [token, save];
}

async function apiFetch(path, { token, method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(API_BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) {
    const msg = formatApiError(data) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

function formatApiError(data) {
  if (!data) return '';
  if (typeof data === 'string') return data;
  const detail = data.detail;
  if (!detail) return '';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => {
      const loc = Array.isArray(e.loc) ? e.loc : [];
      const field = (loc[loc.length - 1] || 'error');
      const reason = (e.ctx && e.ctx.reason) ? e.ctx.reason : e.msg;
      return reason ? `${field}: ${reason}` : String(field);
    }).join('\n');
  }
  return String(detail);
}

function AuthCard({ token, setToken, onAuthed }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    setLoading(true);
    try {
        const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register';
        const data = await apiFetch(path, { method: 'POST', body: { email, password } });
        setToken(data.access_token);
        onAuthed();
    } catch (error) {
        setErr(error.message);
    } finally {
        setLoading(false);
    }
  };

  if (token) {
    return html`
      <div class="glass-card rounded-2xl p-6 transition-all duration-300 shadow-[0_8px_30px_rgb(0,0,0,0.12)]">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
              <i class="ph ph-check-circle text-2xl"></i>
            </div>
            <div>
              <h3 class="font-semibold text-lg text-white">You're connected</h3>
              <p class="text-sm text-gray-400">Ready to start studying</p>
            </div>
          </div>
          <button class="px-5 py-2.5 bg-slate-700/50 hover:bg-slate-600 rounded-xl transition-colors font-medium border border-slate-600 focus:ring-2 focus:ring-slate-500 outline-none flex items-center gap-2 w-full sm:w-auto justify-center text-white" onClick=${() => setToken('')}>
            <i class="ph ph-sign-out text-lg"></i> Sign out
          </button>
        </div>
      </div>
    `;
  }

  return html`
    <div class="glass-card rounded-2xl p-6 transition-all duration-300 shadow-[0_8px_30px_rgb(0,0,0,0.12)]">
      <div class="mb-6 flex border-b border-white/5">
         <button onClick=${()=>setMode('login')} class="pb-3 px-2 text-sm font-medium transition-colors border-b-2 outline-none ${mode==='login' ? 'border-primary text-primary' : 'border-transparent text-gray-400 hover:text-gray-200'} flex-1 flex items-center justify-center gap-2"><i class="ph ph-sign-in text-lg"></i> Login</button>
         <button onClick=${()=>setMode('register')} class="pb-3 px-2 text-sm font-medium transition-colors border-b-2 outline-none ${mode==='register' ? 'border-primary text-primary' : 'border-transparent text-gray-400 hover:text-gray-200'} flex-1 flex items-center justify-center gap-2"><i class="ph ph-user-plus text-lg"></i> Register</button>
      </div>

      ${err && html`
        <div class="mb-5 bg-rose-500/10 border border-rose-500/30 text-rose-300 px-4 py-3 rounded-xl text-sm flex gap-3 items-start animate-fade-in">
          <i class="ph ph-warning-circle text-lg mt-0.5 shrink-0"></i>
          <div class="break-words font-medium">${err}</div>
        </div>
      `}

      <form onSubmit=${submit} class="space-y-4">
        <div class="space-y-1.5">
            <label class="text-xs font-semibold text-gray-400 ml-1 uppercase tracking-wider">Email Address</label>
            <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-500">
                    <i class="ph ph-envelope-simple text-lg"></i>
                </div>
                <input value=${email} onInput=${e => setEmail(e.target.value)} type="email" placeholder="student@example.com" class="w-full bg-slate-900/50 border border-slate-700/50 focus:border-primary focus:ring-1 focus:ring-primary focus:bg-slate-900 rounded-xl px-4 py-3 pl-11 text-sm outline-none transition-all placeholder:text-slate-600 text-white" />
            </div>
        </div>
        
        <div class="space-y-1.5">
            <label class="text-xs font-semibold text-gray-400 ml-1 uppercase tracking-wider">Password</label>
            <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-500">
                    <i class="ph ph-lock-key text-lg"></i>
                </div>
                <input value=${password} onInput=${e => setPassword(e.target.value)} type="password" placeholder="••••••••" maxLength="72" class="w-full bg-slate-900/50 border border-slate-700/50 focus:border-primary focus:ring-1 focus:ring-primary focus:bg-slate-900 rounded-xl px-4 py-3 pl-11 text-sm outline-none transition-all placeholder:text-slate-600 text-white" />
            </div>
        </div>
        
        <button disabled=${!email || !password || loading} type="submit" class="w-full bg-primary hover:bg-primaryHover disabled:opacity-50 disabled:hover:bg-primary shadow-lg shadow-primary/25 text-white font-semibold rounded-xl px-4 py-3.5 transition-all outline-none flex justify-center items-center gap-2 mt-4">
            ${loading ? html`<i class="ph ph-spinner animate-spin text-xl"></i>` : mode === 'login' ? html`<i class="ph ph-sign-in text-xl"></i>` : html`<i class="ph ph-user-plus text-xl"></i>`} 
            ${mode === 'login' ? 'Sign In' : 'Create Account'}
        </button>
      </form>
    </div>
  `;
}

function QuizCard({ token }) {
  const [sets, setSets] = useState([]);
  const [setName, setSetName] = useState('');
  const [mode, setMode] = useState('en-to-ch');
  const [weakOnly, setWeakOnly] = useState(false);

  const [sessionId, setSessionId] = useState('');
  const [question, setQuestion] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [spellText, setSpellText] = useState('');
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastChoice, setLastChoice] = useState(null);

  const authed = !!token;

  const loadSets = async () => {
    setErr('');
    try {
      const data = await apiFetch('/api/sets', { token });
      setSets(data);
      if (!setName && data.length) setSetName(data[0].name);
    } catch(e) {
      setErr(e.message);
    }
  };

  const start = async () => {
    setErr('');
    setFeedback('');
    setLoading(true);
    try {
        const data = await apiFetch('/api/sessions', {
            token,
            method: 'POST',
            body: { set: setName, mode, weak_only: weakOnly },
        });
        setSessionId(data.session_id);
    } catch (error) {
        setErr(error.message);
    } finally {
        setLoading(false);
    }
  };

  const loadQuestion = async (sid) => {
    setErr('');
    setLoading(true);
    try {
        const q = await apiFetch(`/api/sessions/${sid}/question`, { token });
        setQuestion(q);
        setSpellText('');
        setLastChoice(null);
    } catch (error) {
        setErr(error.message);
    } finally {
        setLoading(false);
    }
  };

  const submitChoice = async (choice) => {
    setErr('');
    setLoading(true);
    setLastChoice(choice);
    try {
        const res = await apiFetch(`/api/sessions/${sessionId}/answer`, {
            token,
            method: 'POST',
            body: { choice },
        });
        setFeedback(res.feedback);
        
        // Wait briefly to show colors
        await new Promise(r => setTimeout(r, 700));

        if (res.next_kind === 'spell_retry') await loadQuestion(sessionId);
        if (res.next_kind === 'question') await loadQuestion(sessionId);
        if (res.next_kind === 'finished') {
            const r = await apiFetch(`/api/sessions/${sessionId}/result`, { token });
            setQuestion({ kind: 'finished', prompt: `Quiz Completed!`, result: r });
            setLastChoice(null);
        }
    } catch (error) {
        setErr(error.message);
    } finally {
        setLoading(false);
    }
  };

  const submitSpelling = async (e) => {
    if (e) e.preventDefault();
    if (!spellText.trim()) return;
    
    setErr('');
    setLoading(true);
    try {
        const res = await apiFetch(`/api/sessions/${sessionId}/answer`, {
            token,
            method: 'POST',
            body: { text: spellText },
        });
        setFeedback(res.feedback);
        if (res.next_kind === 'spell_retry') return;
        if (res.next_kind === 'question') await loadQuestion(sessionId);
        if (res.next_kind === 'finished') {
            const r = await apiFetch(`/api/sessions/${sessionId}/result`, { token });
            setQuestion({ kind: 'finished', prompt: `Quiz Completed!`, result: r });
        }
    } catch (error) {
        setErr(error.message);
    } finally {
        setLoading(false);
    }
  };

  const playTts = async () => {
    if (!question) return;
    const text = (question.tts_text || '').trim();
    if (!text) return;
    const url = `/api/tts?text=${encodeURIComponent(text)}`;
    const audio = new Audio(url);
    audio.play();
  };

  useEffect(() => {
    if (authed) loadSets();
  }, [authed]);

  useEffect(() => {
    if (sessionId) loadQuestion(sessionId);
  }, [sessionId]);

  if (!authed) {
    return html`
      <div class="glass-card rounded-2xl p-8 text-center border border-dashed border-white/20 flex flex-col items-center gap-3">
        <i class="ph ph-lock-key text-4xl text-gray-500 mb-2"></i>
        <h3 class="text-xl font-medium text-gray-300">Sign in to play</h3>
        <p class="text-gray-500 text-sm max-w-xs">You need an account to track your progress and start learning new words.</p>
      </div>
    `;
  }

  return html`
    <div class="glass-card rounded-2xl p-6 md:p-8 transition-all duration-300 relative overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.12)]">
      <!-- Decoration bubble -->
      <div class="absolute -top-12 -right-12 w-40 h-40 bg-primary/20 rounded-full blur-[60px] pointer-events-none"></div>

      <div class="flex items-center justify-between gap-3 mb-8 relative z-10 w-full">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-primary/20 text-primary flex items-center justify-center shadow-inner">
            <i class="ph ph-graduation-cap text-2xl"></i>
          </div>
          <h2 class="text-2xl font-bold tracking-tight text-white">Active Quiz</h2>
          ${question && question.progress && html`<span class="ml-2 px-2.5 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-sm font-semibold rounded-lg shadow-inner">${question.progress}</span>`}
        </div>
        ${sessionId && question && html`
          <div class="flex gap-2">
            <button disabled=${loading} onClick=${playTts} class="p-2.5 bg-slate-700/80 hover:bg-slate-600 rounded-lg transition-colors text-white outline-none" title="Listen to pronunciation">
              <i class="ph ph-speaker-high text-lg"></i>
            </button>
            <button disabled=${loading} onClick=${() => { setSessionId(''); setQuestion(null); setFeedback(''); }} class="p-2.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 rounded-lg transition-colors outline-none" title="End Session">
              <i class="ph ph-x text-lg"></i>
            </button>
          </div>
        `}
      </div>
      
      ${err && html`
        <div class="mb-6 bg-rose-500/10 border border-rose-500/30 text-rose-300 px-4 py-3 rounded-xl text-sm flex gap-3 items-start relative z-10">
          <i class="ph ph-warning-circle text-lg mt-0.5 shrink-0"></i>
          <div class="break-words font-medium">${err}</div>
        </div>
      `}

      ${!sessionId && html`
        <div class="space-y-6 relative z-10">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div class="space-y-2 flex flex-col">
                <label class="text-xs font-semibold text-gray-400 ml-1 uppercase tracking-wider">Word Set</label>
                <div class="relative flex-1 text-white">
                    <select value=${setName} onChange=${(e) => setSetName(e.target.value)} class="w-full h-full appearance-none bg-slate-900/50 border border-slate-700/50 focus:border-primary focus:ring-1 focus:ring-primary rounded-xl px-4 py-3 pr-10 text-sm outline-none transition-all cursor-pointer">
                    ${sets.map(s => html`<option key=${s.name} value=${s.name}>${s.name}</option>`)}
                    </select>
                    <i class="ph ph-caret-down text-lg absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"></i>
                </div>
            </div>
            <div class="space-y-2 flex flex-col">
                <label class="text-xs font-semibold text-gray-400 ml-1 uppercase tracking-wider">Play Mode</label>
                <div class="relative flex-1 text-white">
                    <select value=${mode} onChange=${(e) => setMode(e.target.value)} class="w-full h-full appearance-none bg-slate-900/50 border border-slate-700/50 focus:border-primary focus:ring-1 focus:ring-primary rounded-xl px-4 py-3 pr-10 text-sm outline-none transition-all cursor-pointer">
                    <option value="en-to-ch">English → Chinese (MCQ)</option>
                    <option value="ch-to-en">Chinese → English (MCQ)</option>
                    <option value="en-spelling">English spelling</option>
                    </select>
                    <i class="ph ph-caret-down text-lg absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"></i>
                </div>
            </div>
          </div>
          
          <div class="flex items-center justify-between pt-4 border-t border-white/10 flex-wrap gap-4">
              <label class="flex items-center gap-3 cursor-pointer group">
                  <div class="relative flex items-center">
                      <input type="checkbox" checked=${weakOnly} onChange=${(e) => setWeakOnly(e.target.checked)} class="peer sr-only" />
                      <div class="w-11 h-6 bg-slate-700/80 rounded-full peer peer-checked:bg-primary transition-colors duration-300 border border-white/5"></div>
                      <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform duration-300 peer-checked:translate-x-5 shadow-sm"></div>
                  </div>
                  <span class="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">Study weak words only</span>
              </label>
              
              <button onClick=${start} disabled=${!setName || loading} class="w-full sm:w-auto bg-primary hover:bg-primaryHover disabled:opacity-50 text-white font-semibold rounded-xl px-8 py-3.5 transition-all outline-none flex justify-center items-center gap-2 shadow-lg shadow-primary/20">
                  ${loading ? html`<i class="ph ph-spinner animate-spin text-xl"></i>` : html`<i class="ph ph-play-circle text-xl"></i>`} Start Learning
              </button>
          </div>
        </div>
      `}

      ${sessionId && question && html`
        <div class="animate-fade-in relative z-10 transition-all">
          ${question.kind !== 'finished' ? html`
          <div class="text-center py-10 px-4 bg-slate-900/40 rounded-2xl border border-slate-700/50 mb-6 shadow-inner">
            ${question.kind === 'spelling' ? html`<div class="text-sm font-semibold text-primary mb-3 uppercase tracking-wider">Spell the correct word</div>` : null}
            <h3 class="text-4xl sm:text-5xl xl:text-6xl font-bold tracking-tight text-white mb-2 leading-relaxed break-words">${question.prompt}</h3>
          </div>
          ` : null}

          ${question.kind === 'multiple_choice' && html`
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
              ${(question.choices || []).map((c, idx) => {
                const isSelected = lastChoice === (idx + 1);
                const isFeedbackVisible = feedback && isSelected;
                const isCorrect = feedback.startsWith('Correct');
                let btnCls = "text-left bg-slate-800/80 hover:bg-slate-700 border border-slate-600/50 hover:border-primary/50 text-gray-200 hover:text-white rounded-xl p-4 sm:p-5 transition-all duration-200 group flex items-start gap-4";
                let numCls = "w-8 h-8 rounded-lg bg-slate-900 text-slate-400 flex items-center justify-center text-sm font-bold group-hover:bg-primary group-hover:text-white transition-colors shrink-0 shadow-inner";
                
                if (isFeedbackVisible) {
                  if (isCorrect) {
                     btnCls = "text-left bg-emerald-500/10 border border-emerald-500/50 text-emerald-400 rounded-xl p-4 sm:p-5 transition-all duration-200 flex items-start gap-4 shadow-[0_0_15px_rgba(16,185,129,0.15)]";
                     numCls = "w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm font-bold shrink-0 text-emerald-300";
                  } else {
                     btnCls = "text-left bg-rose-500/10 border border-rose-500/50 text-rose-400 rounded-xl p-4 sm:p-5 transition-all duration-200 flex items-start gap-4 shadow-[0_0_15px_rgba(244,63,94,0.15)]";
                     numCls = "w-8 h-8 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center text-sm font-bold shrink-0 text-rose-300";
                  }
                }

                return html`
                <button key=${idx} disabled=${loading} onClick=${() => submitChoice(idx + 1)} class=${btnCls}>
                  <span class=${numCls}>${idx + 1}</span>
                  <span class="font-medium text-lg mt-0.5 leading-snug">${c}</span>
                </button>
              `})}
            </div>
          `}

          ${question.kind === 'spelling' && html`
            <form onSubmit=${submitSpelling} class="mt-8 flex flex-col sm:flex-row gap-3">
              <div class="relative flex-1">
                  <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-500">
                      <i class="ph ph-keyboard text-xl"></i>
                  </div>
                  <input value=${spellText} onInput=${(e) => setSpellText(e.target.value)} type="text" placeholder="Type the correct spelling..." class="w-full bg-slate-900/50 border border-slate-700/50 focus:border-primary focus:ring-1 focus:ring-primary rounded-xl px-4 py-4 pl-12 shadow-[inset_0_2px_4px_rgba(0,0,0,0.6)] outline-none transition-all text-white placeholder:text-slate-600 text-lg sm:text-xl" autoFocus />
              </div>
              <button disabled=${loading || !spellText} type="submit" class="bg-primary hover:bg-primaryHover disabled:opacity-50 text-white font-bold rounded-xl px-8 py-4 transition-all outline-none flex justify-center items-center gap-2 shadow-lg shadow-primary/20 shrink-0 text-lg">
                ${loading ? html`<i class="ph ph-spinner animate-spin text-2xl"></i>` : html`Check <i class="ph ph-arrow-right text-xl"></i>`}
              </button>
            </form>
          `}

          ${(feedback && question.kind !== 'finished') ? html`
            <div class="mt-8 p-4 rounded-xl flex items-center justify-center gap-3 text-center ${feedback.startsWith('Correct') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}">
              <i class="ph ${feedback.startsWith('Correct') ? 'ph-check-circle' : 'ph-x-circle'} text-2xl"></i>
              <span class="font-medium text-[15px]">${feedback}</span>
            </div>
          ` : null}

          ${question.kind === 'finished' && question.result && html`
            <div class="text-center py-8">
              <div class="inline-flex w-24 h-24 rounded-full bg-primary/20 items-center justify-center mb-6 shadow-[0_0_40px_rgba(59,130,246,0.3)]">
                <i class="ph-fill ph-trophy text-5xl text-primary"></i>
              </div>
              <h3 class="text-2xl font-bold text-white mb-8">Quiz Completed!</h3>
              <div class="grid grid-cols-3 gap-4 mb-10 w-full max-w-md mx-auto">
                <div class="bg-slate-800/80 rounded-2xl p-5 border border-emerald-500/20 shadow-lg">
                    <div class="text-4xl font-bold text-emerald-400 mb-2">${question.result.correct}</div>
                    <div class="text-xs uppercase tracking-widest text-emerald-200/50 font-bold">Correct</div>
                </div>
                <div class="bg-slate-800/80 rounded-2xl p-5 border border-rose-500/20 shadow-lg">
                    <div class="text-4xl font-bold text-rose-400 mb-2">${question.result.wrong}</div>
                    <div class="text-xs uppercase tracking-widest text-rose-200/50 font-bold">Wrong</div>
                </div>
                <div class="bg-slate-800/80 rounded-2xl p-5 border border-primary/20 shadow-lg">
                    <div class="text-4xl font-bold text-primary mb-2">${question.result.accuracy}</div>
                    <div class="text-xs uppercase tracking-widest text-blue-200/50 font-bold">Accuracy %</div>
                </div>
              </div>
              <button onClick=${() => { setSessionId(''); setQuestion(null); setFeedback(''); }} class="bg-slate-700 hover:bg-slate-600 border border-slate-600 shadow-xl text-white font-semibold rounded-xl px-8 py-4 transition-all outline-none flex mx-auto items-center gap-2 text-lg">
                <i class="ph ph-arrow-counter-clockwise text-xl"></i> Practice Again
              </button>
            </div>
          `}
        </div>
      `}
    </div>
  `;
}



function StatsCard({ token }) {
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState('');
  
  const loadStats = async () => {
    setErr('');
    try {
      const data = await apiFetch('/api/stats', { token });
      setStats(data);
    } catch(e) {
      setErr(e.message);
    }
  };

  useEffect(() => {
    if (token) loadStats();
  }, [token]);

  if (!token) return html`<div>Loading...</div>`;

  return html`
    <div class="glass-card rounded-2xl p-6 sm:p-8 animate-fade-in">
      <div class="flex items-center gap-3 mb-6">
        <i class="ph-fill ph-chart-bar text-2xl text-blue-400"></i>
        <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">Your Statistics</h2>
      </div>
      
      ${err && html`<p class="text-rose-400">${err}</p>`}
      
      ${stats && html`
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <div class="bg-indigo-500/10 border border-indigo-500/20 p-4 rounded-xl flex items-center gap-4">
            <div class="w-12 h-12 bg-indigo-500/20 rounded-full flex items-center justify-center text-indigo-400"><i class="ph-bold ph-calendar text-2xl"></i></div>
            <div>
              <p class="text-sm font-semibold text-gray-400 uppercase tracking-wider">Total Quizzes</p>
              <p class="text-2xl font-bold text-white">${stats.total_sessions}</p>
            </div>
          </div>
          
          <div class="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl flex items-center gap-4">
            <div class="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400"><i class="ph-bold ph-target text-2xl"></i></div>
            <div>
              <p class="text-sm font-semibold text-gray-400 uppercase tracking-wider">Avg Accuracy</p>
              <p class="text-2xl font-bold text-white">${stats.average_accuracy}%</p>
            </div>
          </div>
        </div>
        
        <h3 class="text-lg font-bold text-white mb-4 border-b border-white/10 pb-2">Top Weak Words</h3>
        ${stats.top_wrong && stats.top_wrong.length ? html`
          <div class="space-y-2">
            ${stats.top_wrong.map((ww, i) => html`
              <div class="flex items-start sm:items-center gap-3 bg-slate-800/50 p-3.5 rounded-lg border border-slate-700/50">
                <div class="w-7 h-7 shrink-0 bg-slate-900 rounded text-slate-400 flex items-center justify-center text-sm font-bold mt-0.5 sm:mt-0">${i+1}</div>
                <div class="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                  <span class="text-lg font-medium text-gray-200 sm:w-[35%] shrink-0 truncate" title=${ww.en}>${ww.en}</span>
                  <span class="text-gray-400 text-[15px] flex-1 line-clamp-2 text-left" title=${ww.ch}>${ww.ch}</span>
                </div>
                <div class="shrink-0 pt-0.5 sm:pt-0">
                  <span class="bg-rose-500/20 text-rose-400 px-2.5 py-1 rounded-md text-[13px] font-bold shadow-inner shadow-rose-500/10 whitespace-nowrap">× ${ww.count}</span>
                </div>
              </div>
            `)}
          </div>
        ` : html`<p class="text-green-400 font-medium">You don't have any recorded weak words. Great job!</p>`}
      `}
    </div>
  `;
}

function VocabCard({ token }) {
  const [sets, setSets] = useState([]);
  const [setName, setSetName] = useState('');
  const [vocab, setVocab] = useState([]);
  const [err, setErr] = useState('');
  
  const [newWord, setNewWord] = useState('');
  const [newTrans, setNewTrans] = useState('');
  const [loading, setLoading] = useState(false);

  const loadSets = async () => {
    setErr('');
    try {
      const data = await apiFetch('/api/sets', { token });
      setSets(data);
      if (!setName && data.length) setSetName(data[0].name);
    } catch(e) {
      setErr(e.message);
    }
  };

  const loadVocab = async () => {
    if (!setName) return;
    setErr('');
    setLoading(true);
    try {
      const data = await apiFetch(`/api/sets/${setName}/vocab`, { token });
      setVocab(data);
    } catch(e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSets(); }, [token]);
  useEffect(() => { loadVocab(); }, [setName]);

  const addVocab = async (e) => {
    e.preventDefault();
    if (!newWord || !newTrans) return;
    setErr('');
    setLoading(true);
    try {
      await apiFetch(`/api/sets/${setName}/vocab`, {
        method: 'POST',
        token,
        body: { word: newWord, translation: newTrans }
      });
      setNewWord('');
      setNewTrans('');
      await loadVocab();
    } catch(e) {
      setErr(e.message);
      setLoading(false);
    }
  };
  
  const delVocab = async (word) => {
    if (!confirm(`Delete ${word}?`)) return;
    setErr('');
    setLoading(true);
    try {
      await apiFetch(`/api/sets/${setName}/vocab/${word}`, {
        method: 'DELETE',
        token
      });
      await loadVocab();
    } catch(e) {
      setErr(e.message);
      setLoading(false);
    }
  };

  return html`
    <div class="glass-card rounded-2xl p-6 sm:p-8 animate-fade-in shadow-[0_8px_30px_rgb(0,0,0,0.12)]">
      <div class="flex items-center gap-3 mb-6">
        <i class="ph-fill ph-book-open-text text-2xl text-teal-400"></i>
        <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-emerald-400">Vocab Sets</h2>
      </div>

      ${err && html`<div class="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 p-3 rounded-lg text-sm">${err}</div>`}

      <div class="mb-6 flex items-end gap-3 flex-wrap">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">Select Set</label>
          <select value=${setName} onChange=${e => setSetName(e.target.value)} class="w-full bg-slate-900/80 border border-slate-700/50 rounded-xl px-4 py-3 outline-none focus:border-teal-400 focus:ring-1 focus:ring-teal-400 text-white font-medium shadow-inner appearance-none relative">
            ${sets.map(s => html`<option key=${s.name} value=${s.name}>${s.name}</option>`)}
          </select>
        </div>
      </div>
      
      <form onSubmit=${addVocab} class="flex gap-4 items-center mb-6 bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex-wrap sm:flex-nowrap">
          <input type="text" value=${newWord} onChange=${e=>setNewWord(e.target.value)} placeholder="New Word" class="flex-1 bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 text-white outline-none focus:border-teal-400" required />
          <input type="text" value=${newTrans} onChange=${e=>setNewTrans(e.target.value)} placeholder="Translation" class="flex-1 bg-slate-900/50 border border-slate-600/50 rounded-lg px-3 py-2 text-white outline-none focus:border-teal-400" required />
          <button type="submit" disabled=${loading || !newWord || !newTrans} class="bg-teal-500 hover:bg-teal-400 w-full sm:w-auto text-white rounded-lg px-4 py-2 font-bold shadow-lg disabled:opacity-50 transition-colors flex items-center justify-center gap-2"><i class="ph ph-plus-circle text-lg"></i> Add</button>
      </form>

      <div class="max-h-96 overflow-y-auto pr-2 rounded-lg border border-slate-700/30">
        ${vocab.length === 0 ? html`<p class="text-gray-400 text-center p-4">Empty set.</p>` : html`
          <table class="w-full text-left text-gray-300">
            <thead class="sticky top-0 bg-slate-800/90 backdrop-blur text-sm uppercase text-gray-400 shadow">
              <tr><th class="p-3 font-semibold">Word</th><th class="p-3 font-semibold">Translation</th><th class="p-3 font-semibold text-right">Delete</th></tr>
            </thead>
            <tbody class="divide-y divide-slate-700/50">
              ${vocab.map(v => html`
                <tr class="hover:bg-slate-800/30 transition-colors">
                  <td class="p-3 font-medium text-white">${v.word}</td>
                  <td class="p-3 text-sm">${v.translation}</td>
                  <td class="p-3 text-right">
                      <button onClick=${()=>delVocab(v.word)} class="text-slate-500 hover:text-rose-400 transition-colors p-1" title="Delete"><i class="ph ph-trash text-lg"></i></button>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        `}
      </div>
    </div>
  `;
}




function App() {
  const [token, setToken] = useStoredToken();
  const [me, setMe] = useState(null);
  const [tab, setTab] = useState('quiz'); // quiz, stats, vocab
  const authed = !!token;

  const refreshMe = async () => {
    if (!token) { setMe(null); return; }
    try {
        const data = await apiFetch('/api/auth/me', { token });
        setMe(data);
    } catch (e) {
        setMe(null);
    }
  };

  useEffect(() => { refreshMe(); }, [token]);

  return html`
    <div class="min-h-screen px-4 py-8 sm:py-12 md:py-16 relative">
      <div class="fixed top-0 inset-x-0 h-1 bg-gradient-to-r from-blue-600 via-indigo-500 to-teal-400"></div>
      <div class="max-w-5xl mx-auto space-y-8 relative z-10">
        
        <header class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 pb-2 mb-8">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <div class="bg-gradient-to-br from-blue-500 to-indigo-600 text-white p-2.5 rounded-xl shadow-lg shadow-blue-500/30">
                <i class="ph-fill ph-books text-2xl"></i>
              </div>
              <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-white drop-shadow-sm">Wordly<span class="text-primary text-4xl leading-none">.</span></h1>
            </div>
            <p class="text-gray-400 text-[15px] font-medium ml-1">Master your vocabulary with smart quizzes.</p>
          </div>
          
          ${me && html`
            <div class="flex items-center gap-3 bg-slate-800/80 px-5 py-2.5 rounded-full border border-slate-700/50 shadow-lg backdrop-blur-md">
              <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-indigo-400 flex items-center justify-center text-white text-sm font-bold shadow-inner">
                ${me.email.charAt(0).toUpperCase()}
              </div>
              <span class="text-sm font-medium text-gray-200">${me.email}</span>
            </div>
          `}
        </header>

        <main class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div class="lg:col-span-4 space-y-8">
            <${AuthCard} token=${token} setToken=${setToken} onAuthed=${refreshMe} />
            
            ${authed && html`
              <div class="flex flex-col gap-2">
                  <button onClick=${()=>setTab('quiz')} class="text-left px-5 py-3 rounded-xl transition-all font-bold tracking-wide text-sm flex items-center gap-3 ${tab==='quiz' ? 'bg-primary shadow-lg text-white' : 'bg-slate-800/50 text-gray-400 hover:bg-slate-700/50 hover:text-white'}">
                      <i class="ph ph-game-controller text-xl"></i> Active Quiz
                  </button>
                  <button onClick=${()=>setTab('stats')} class="text-left px-5 py-3 rounded-xl transition-all font-bold tracking-wide text-sm flex items-center gap-3 ${tab==='stats' ? 'bg-blue-500 shadow-lg text-white' : 'bg-slate-800/50 text-gray-400 hover:bg-slate-700/50 hover:text-white'}">
                      <i class="ph ph-chart-bar text-xl"></i> Statistics
                  </button>
                  <button onClick=${()=>setTab('vocab')} class="text-left px-5 py-3 rounded-xl transition-all font-bold tracking-wide text-sm flex items-center gap-3 ${tab==='vocab' ? 'bg-teal-500 shadow-lg text-white' : 'bg-slate-800/50 text-gray-400 hover:bg-slate-700/50 hover:text-white'}">
                      <i class="ph ph-book-open-text text-xl"></i> Vocab Sets
                  </button>
              </div>
            `}

            <div class="glass-card rounded-2xl p-7 relative overflow-hidden hidden lg:block shadow-[0_8px_30px_rgb(0,0,0,0.12)] border-l-4 border-l-indigo-500">
              <div class="absolute -top-4 -right-4 text-white/5 text-[100px] pointer-events-none transform rotate-12">
                <i class="ph-fill ph-lightbulb"></i>
              </div>
              <div class="flex items-center gap-2 mb-3">
                  <i class="ph-fill ph-lightbulb text-indigo-400 text-xl"></i>
                  <h4 class="font-bold text-gray-200 relative z-10 uppercase tracking-wider text-xs">Daily Tip</h4>
              </div>
              <p class="text-[15px] text-gray-300 relative z-10 leading-relaxed font-medium">"Consistent practice is better than cramming. Spending 10 minutes a day on weak words boosts retention by 40%."</p>
            </div>
          </div>
          
          <div class="lg:col-span-8">
            ${authed ? html`
              ${tab === 'quiz' && html`<${QuizCard} token=${token} />`}
              ${tab === 'stats' && html`<${StatsCard} token=${token} />`}
              ${tab === 'vocab' && html`<${VocabCard} token=${token} />`}
            ` : html`
              <div class="glass-card rounded-3xl overflow-hidden border border-white/5 flex flex-col items-center justify-center p-12 text-center shadow-lg h-full">
                <div class="w-20 h-20 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center mb-6 shadow-inner text-slate-400">
                    <i class="ph ph-lock-key text-4xl"></i>
                </div>
                <h3 class="text-2xl font-bold tracking-tight text-white mb-3">Authentication Required</h3>
                <p class="text-gray-400 text-base max-w-sm mb-8 leading-relaxed">Please sign in or create an account to start your vocabulary journey.</p>
              </div>
            `}
          </div>
        </main>
        
        <footer class="pt-16 pb-4 text-center text-sm text-gray-500 font-medium flex justify-center gap-6">
            <span class="flex items-center gap-1.5"><i class="ph-fill ph-lightning text-primary"></i> FastAPI</span>
            <span class="flex items-center gap-1.5"><i class="ph-fill ph-atom text-teal-400"></i> React</span>
            <span class="flex items-center gap-1.5"><i class="ph-fill ph-wind text-sky-400"></i> TailwindCSS</span>
        </footer>
      </div>
    </div>
  `;
}


createRoot(document.getElementById('root')).render(React.createElement(App));
