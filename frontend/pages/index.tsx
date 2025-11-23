import { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

type ChatSource = { name: string; source_type: string; snippet: string };
type ChatMessage = { role: 'user' | 'assistant'; content: string; sources?: ChatSource[] };
type SourceItem = { name: string; source_type: string; created_at: string };

export default function Home() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [urls, setUrls] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sourceType, setSourceType] = useState<string>('');
  const [topK, setTopK] = useState<number>(4);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [enableMcp, setEnableMcp] = useState(false);

  const fetchSources = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/sources`);
      setSources(res.data);
    } catch (err) {
      console.error('Failed to fetch sources', err);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleFileUpload = async () => {
    if (!files || files.length === 0) return;
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    await axios.post(`${API_BASE}/api/ingest/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    setFiles(null);
    fetchSources();
  };

  const handleUrlIngest = async () => {
    const urlList = urls.split(/\n|,/).map((u) => u.trim()).filter(Boolean);
    if (urlList.length === 0) return;
    await axios.post(`${API_BASE}/api/ingest/urls`, { urls: urlList });
    setUrls('');
    fetchSources();
  };

  const handleSend = async () => {
    if (!chatInput.trim()) return;
    const userMessage: ChatMessage = { role: 'user', content: chatInput };
    setMessages((prev) => [...prev, userMessage]);
    setChatInput('');
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/chat`, {
        message: userMessage.content,
        source_type: sourceType || null,
        top_k: topK,
        enable_mcp: enableMcp,
      });
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Chat failed', err);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Request failed' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout">
      <header>
        <div>
          <p className="eyebrow">Company Knowledge Copilot</p>
          <h1>Centralize documents, URLs, and MCP feeds into one AI assistant.</h1>
          <p className="lede">Upload policies, paste docs URLs, sync MCP sources, then ask questions with grounded citations.</p>
        </div>
      </header>

      <main className="grid">
        <section className="card ingest">
          <h2>Ingest sources</h2>
          <div className="ingest-block">
            <label className="label">Files (PDF, DOCX, TXT, MD)</label>
            <div className="upload">
              <input type="file" multiple onChange={(e) => setFiles(e.target.files)} />
              <button onClick={handleFileUpload}>Upload &amp; Embed</button>
            </div>
          </div>
          <div className="ingest-block">
            <label className="label">URLs (one per line)</label>
            <textarea value={urls} onChange={(e) => setUrls(e.target.value)} placeholder="https://docs.example.com/guide" />
            <button onClick={handleUrlIngest}>Ingest URLs</button>
          </div>
          <div className="ingest-block">
            <p className="hint">MCP GitHub mirror is ingested automatically when toggled in chat.</p>
          </div>
          <div className="sources">
            <h3>Indexed sources</h3>
            {sources.length === 0 && <p className="muted">No sources ingested yet.</p>}
            {sources.map((s) => (
              <div key={`${s.name}-${s.created_at}`} className="pill">
                <span>{s.name}</span>
                <span className="muted">{s.source_type}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="card chat">
          <h2>Ask anything</h2>
          <div className="controls">
            <label>
              Source filter
              <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                <option value="">All</option>
                <option value="file">Files</option>
                <option value="url">URLs</option>
                <option value="mcp-github">MCP GitHub</option>
              </select>
            </label>
            <label>
              Top K
              <input type="number" min={1} max={10} value={topK} onChange={(e) => setTopK(Number(e.target.value))} />
            </label>
            <label className="toggle">
              <input type="checkbox" checked={enableMcp} onChange={(e) => setEnableMcp(e.target.checked)} />
              <span>Sync MCP GitHub before answering</span>
            </label>
          </div>
          <div className="chat-window">
            {messages.map((m, idx) => (
              <div key={idx} className={`bubble ${m.role}`}>
                <div className="bubble-header">{m.role === 'user' ? 'You' : 'Copilot'}</div>
                <p>{m.content}</p>
                {m.sources && (
                  <div className="sources-list">
                    {m.sources.map((s, i) => (
                      <div key={i} className="source-chip">
                        <strong>{s.name}</strong>
                        <span>{s.source_type}</span>
                        <p>{s.snippet}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && <div className="bubble assistant">Thinking...</div>}
          </div>
          <div className="chat-input">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about policies, SOPs, FAQs..."
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend} disabled={loading}>Send</button>
          </div>
        </section>
      </main>
    </div>
  );
}
