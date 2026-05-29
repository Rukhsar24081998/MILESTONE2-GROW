# Phase 4 Frontend - User Interface Guide

## 🚀 Quick Start

### 1. Start the Backend API
```bash
# Terminal 1 - Start FastAPI backend
cd "/Users/rukhsarkhan/Mileston2 "
.venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend
```bash
# Terminal 2 - Serve UI
cd "/Users/rukhsarkhan/Mileston2 /ui"
python3 -m http.server 5173
```

### 3. Open in Browser
```
http://localhost:5173
```

---

## 🎨 UI Features

### 1. **Disclaimer Banner** (Top)
- Persistent purple gradient banner
- Clear message: "Facts Only: No investment advice"
- Visible on all pages

### 2. **Welcome Section**
- Title: "Mutual Fund FAQ Assistant"
- Scope explanation
- Coverage info (5 HDFC schemes)
- Groww-inspired clean design

### 3. **Corpus Status Bar**
- Shows document count (5 schemes)
- Last update date
- Corpus version
- Real-time status from `/corpus/status`

### 4. **Example Question Chips**
- 3 clickable example questions
- Gradient purple buttons with hover effects
- Auto-loads from `/examples` API
- Click to instantly ask

### 5. **Chat Interface**
- **Message Display:**
  - User messages (right-aligned, purple gradient)
  - Bot messages (left-aligned, white cards)
  - Refusals (yellow background for visibility)
  
- **Citation Links:**
  - Clickable "View source on Groww" button
  - Opens in new tab
  - Only shown for factual answers
  
- **Footer Dates:**
  - Shows "Last updated from sources: <date>"
  - Italic, gray text
  - On every bot response

### 6. **Input Area**
- Text input with placeholder
- Send button (gradient purple)
- Enter key support
- 500 character limit
- Disabled during loading

### 7. **Loading States**
- Animated bouncing dots
- Input disabled while processing
- Button shows loading state

### 8. **Error Handling**
- Red error banners
- Auto-dismiss after 5 seconds
- User-friendly messages

---

## 📱 Responsive Design

- **Desktop:** Full-width chat (max 800px)
- **Mobile:** Adapted layout, smaller fonts
- **Tablet:** Balanced spacing

---

## 🎯 User Flow

```
1. User opens http://localhost:5173
   ↓
2. Sees disclaimer banner + welcome message
   ↓
3. Views corpus status (5 schemes loaded)
   ↓
4. Clicks example chip OR types question
   ↓
5. Question appears in chat (purple, right)
   ↓
6. Loading indicator shows (bouncing dots)
   ↓
7. Response appears (white card, left)
   ├─ If answer: Shows citation link + footer
   └─ If refusal: Yellow background, no URL
   ↓
8. User can ask another question
```

---

## 🧪 Testing Checklist

### ✅ Visual Elements
- [ ] Disclaimer banner visible at top
- [ ] Welcome section displays correctly
- [ ] Corpus status shows 5 schemes
- [ ] 3 example chips appear
- [ ] Chat interface loads
- [ ] Input field and send button work

### ✅ Functionality
- [ ] Click example chip → auto-asks question
- [ ] Type question + Enter → sends
- [ ] Type question + Click Send → sends
- [ ] Loading indicator appears during processing
- [ ] User message shows immediately (purple)
- [ ] Bot response appears with proper styling

### ✅ Response Types
- [ ] Factual answer shows citation link
- [ ] Factual answer shows footer date
- [ ] Refusal shows yellow background
- [ ] Refusal has NO citation link
- [ ] Refusal shows reason

### ✅ Error Handling
- [ ] Empty query → no action
- [ ] Short query (<3 chars) → error message
- [ ] API down → error message displayed
- [ ] Network error → user-friendly message

### ✅ Edge Cases
- [ ] HTML in query → stripped safely
- [ ] Very long query (500 chars) → accepted
- [ ] Rapid clicking → disabled during loading
- [ ] Multiple questions → all visible in scroll

---

## 🎨 Design System

### Colors
- **Primary Gradient:** `#667eea` → `#764ba2` (purple)
- **Background:** `#f5f5f5` (light gray)
- **Cards:** `#ffffff` (white)
- **User Messages:** Purple gradient
- **Bot Messages:** White with border
- **Refusals:** `#fff3cd` (yellow)
- **Errors:** `#f8d7da` (red)

### Typography
- **Font:** System fonts (-apple-system, BlinkMacSystemFont, etc.)
- **Headings:** 28px, 20px
- **Body:** 15-16px
- **Small:** 12-14px

### Spacing
- **Container:** Max 800px, centered
- **Cards:** 20-30px padding
- **Messages:** 20px gap
- **Chips:** 12px gap

---

## 🔗 API Integration

### Endpoints Used
```javascript
GET  /examples       → Load example chips
GET  /corpus/status  → Show corpus info
POST /ask            → Process questions
```

### Request Format
```javascript
{
  "query": "What is the expense ratio?"
}
```

### Response Format
```javascript
{
  "type": "answer" | "refusal",
  "text": "Response text...",
  "citation_url": "https://...", // or null
  "footer": "Last updated from sources: 2026-05-28",
  "refused": true | false
}
```

---

## 🚀 Deployment

### Local Development
```bash
# Terminal 1 - API
.venv/bin/uvicorn app.api.main:app --port 8000

# Terminal 2 - UI
cd ui && python3 -m http.server 5173
```

### Production (Future)
- Deploy API to cloud (AWS, GCP, Render)
- Serve UI via CDN (Cloudflare, Netlify, Vercel)
- Update `API_BASE` in `index.html`
- Add HTTPS

---

## 📝 Architecture Compliance

✅ **Disclaimer Banner** - Phase 4 requirement  
✅ **Welcome Message** - Explains facts-only scope  
✅ **Example Questions** - 3 chips from API  
✅ **Chat Interface** - Input + message list  
✅ **Citation Links** - Clickable, opens in new tab  
✅ **Footer Dates** - On every bot message  
✅ **Error States** - Network failure, empty retrieval  
✅ **No PII Collection** - Stateless, no user accounts  
✅ **Facts-Only** - Clear messaging throughout  

---

## 🎯 Next Steps (Phase 5+)

1. **Rate Limiting** - Add per-IP limits
2. **Response Caching** - Cache frequent queries
3. **Analytics** - Track usage (no PII)
4. **Dark Mode** - Toggle theme
5. **Chat History** - Local storage
6. **Mobile App** - React Native wrapper
7. **Accessibility** - ARIA labels, keyboard nav

---

**Phase 4 Frontend is complete and ready for user testing!** 🎉
