# React Patterns — Deep Reference

## Table of Contents
1. [useEffect Anti-Patterns](#useeffect)
2. [State Management Issues](#state)
3. [Performance Traps](#performance)
4. [Security Issues](#security)
5. [Accessibility Red Flags](#a11y)
6. [TypeScript in React](#typescript)

---

## 1. useEffect Anti-Patterns {#useeffect}

### ❌ Async directly in useEffect callback
```tsx
// WRONG — React will warn, and the cleanup return is ignored
useEffect(async () => {
  const data = await fetchData();
  setData(data);
}, []);

// ✅ CORRECT
useEffect(() => {
  let cancelled = false;
  async function load() {
    const data = await fetchData();
    if (!cancelled) setData(data);
  }
  load();
  return () => { cancelled = true; };
}, []);
```

### ❌ Object/Array dependencies cause infinite loops
```tsx
// WRONG — new object reference every render = infinite loop
useEffect(() => { fetchUser(options); }, [{ id: userId }]);

// ✅ CORRECT — use primitives as deps
useEffect(() => { fetchUser({ id: userId }); }, [userId]);
```

### ❌ Missing cleanup for subscriptions
```tsx
// WRONG — memory leak
useEffect(() => {
  window.addEventListener('resize', handleResize);
}, []);

// ✅ CORRECT
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, [handleResize]);
```

### ❌ Derived state in useEffect (anti-pattern)
```tsx
// WRONG — sync state with effect
const [filtered, setFiltered] = useState([]);
useEffect(() => {
  setFiltered(items.filter(x => x.active));
}, [items]);

// ✅ CORRECT — compute directly
const filtered = useMemo(() => items.filter(x => x.active), [items]);
// Or for simple cases: const filtered = items.filter(x => x.active);
```

---

## 2. State Management Issues {#state}

### ❌ Direct state mutation
```tsx
// WRONG — React won't detect this change
const [items, setItems] = useState([]);
items.push(newItem); // mutation!
setItems(items);

// ✅ CORRECT
setItems(prev => [...prev, newItem]);
```

### ❌ Stale closure in event handlers
```tsx
// WRONG — count is stale inside the callback
const [count, setCount] = useState(0);
const increment = () => {
  setTimeout(() => setCount(count + 1), 1000); // stale!
};

// ✅ CORRECT — functional update
const increment = () => {
  setTimeout(() => setCount(prev => prev + 1), 1000);
};
```

### ❌ State initialization from props (source of truth conflict)
```tsx
// WRONG — prop changes won't update state
const [name, setName] = useState(props.name);

// ✅ CORRECT — if you need derived local state, use useEffect + key reset
// or just use props.name directly if it doesn't need local mutation
```

---

## 3. Performance Traps {#performance}

### ❌ Creating new references in JSX
```tsx
// WRONG — new object on every render defeats memoization
<Child style={{ color: 'red' }} onClick={() => handleClick(id)} />

// ✅ CORRECT
const style = useMemo(() => ({ color: 'red' }), []);
const handleClickMemo = useCallback(() => handleClick(id), [id, handleClick]);
<Child style={style} onClick={handleClickMemo} />
```

### ❌ Context with frequently-changing values
```tsx
// WRONG — every consumer re-renders on any theme change
const AppContext = createContext({ user, theme, cart, notifications });

// ✅ CORRECT — split into focused contexts
const UserContext = createContext(user);
const ThemeContext = createContext(theme);
```

### ❌ Key using array index for reorderable lists
```tsx
// WRONG — causes wrong component to get state
{items.map((item, i) => <Item key={i} {...item} />)}

// ✅ CORRECT
{items.map(item => <Item key={item.id} {...item} />)}
```

---

## 4. Security Issues {#security}

### ❌ dangerouslySetInnerHTML with user content
```tsx
// WRONG — XSS attack vector
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ CORRECT — sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userContent) }} />
```

### ❌ href with user-provided URLs
```tsx
// WRONG — javascript: protocol attack
<a href={user.website}>Profile</a>

// ✅ CORRECT
const safeHref = user.website?.startsWith('http') ? user.website : '#';
<a href={safeHref} rel="noopener noreferrer" target="_blank">Profile</a>
```

---

## 5. Accessibility Red Flags {#a11y}

```tsx
// ❌ Click handler on non-interactive element
<div onClick={handleClick}>Click me</div>

// ✅ Use button or add role + keyboard support
<button onClick={handleClick}>Click me</button>
// OR
<div role="button" tabIndex={0} onClick={handleClick} onKeyDown={e => e.key === 'Enter' && handleClick()}>

// ❌ Image without alt
<img src={avatar} />

// ✅ Descriptive alt or empty for decorative
<img src={avatar} alt="User avatar" />
<img src={decoration} alt="" />

// ❌ Form inputs without labels
<input type="text" placeholder="Email" />

// ✅ Explicit label association
<label htmlFor="email">Email</label>
<input id="email" type="email" />
```

---

## 6. TypeScript in React {#typescript}

```tsx
// ❌ Weak event handler types
const handleChange = (e: any) => setVal(e.target.value);

// ✅ Precise types
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => setVal(e.target.value);

// ❌ No children type
interface Props { label: string }

// ✅ Explicit children
interface Props { label: string; children: React.ReactNode }

// ❌ useRef without type
const ref = useRef(null);

// ✅ Typed ref
const ref = useRef<HTMLDivElement>(null);

// ❌ useState with wrong initial value type
const [user, setUser] = useState(null); // inferred as null

// ✅ Explicit generic
const [user, setUser] = useState<User | null>(null);
```
