# Advanced TSX / React TypeScript Patterns for Refactoring

## Table of Contents
1. [Component Splitting](#component-splitting)
2. [Props Typing Patterns](#props-typing)
3. [Custom Hook Extraction](#hook-extraction)
4. [Event Handler Typing](#events)
5. [Context Typing](#context)
6. [Performance Patterns](#performance)
7. [Render Optimization](#render)
8. [Testing Patterns](#testing)

---

## 1. Component Splitting {#component-splitting}

### When and how to split
```tsx
// ❌ Before: god component (too long, too many concerns)
export function UserDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { /* fetch user */ }, []);
  useEffect(() => { /* fetch posts */ }, [user]);

  const handleLike = (postId: string) => { /* ... */ };
  const handleDelete = (postId: string) => { /* ... */ };

  return (
    <div>
      {/* 100+ lines of JSX */}
    </div>
  );
}

// ✅ After: split by concern
// hooks/useUserDashboard.ts
export function useUserDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // fetch logic...
  return { user, isLoading, error };
}

// hooks/useUserPosts.ts
export function useUserPosts(userId: string | undefined) {
  const [posts, setPosts] = useState<Post[]>([]);
  // fetch + handlers...
  return { posts, handleLike, handleDelete };
}

// UserDashboard.tsx (thin orchestrator)
export function UserDashboard() {
  const { user, isLoading, error } = useUserDashboard();
  const { posts, handleLike, handleDelete } = useUserPosts(user?.id);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!user) return null;

  return (
    <div>
      <UserHeader user={user} />
      <PostList posts={posts} onLike={handleLike} onDelete={handleDelete} />
    </div>
  );
}
```

---

## 2. Props Typing Patterns {#props-typing}

```tsx
// Pattern: extend HTML element props
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  isLoading?: boolean;
}

// Pattern: discriminated prop union
type AlertProps =
  | { type: 'error'; message: string; onRetry: () => void }
  | { type: 'info'; message: string; onRetry?: never }
  | { type: 'success'; message: string; onRetry?: never };

// Pattern: children with specific type
interface LayoutProps {
  children: React.ReactNode;         // any renderable content
  header: React.ReactElement;        // must be a JSX element
  footer?: React.ReactElement;       // optional JSX element
}

// Pattern: render prop
interface ListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  keyExtractor: (item: T) => string;
}

// Pattern: polymorphic component (as prop)
type AsProp<C extends React.ElementType> = {
  as?: C;
};
type PropsWithAs<C extends React.ElementType, P = {}> =
  P & AsProp<C> & Omit<React.ComponentPropsWithRef<C>, keyof (P & AsProp<C>)>;
```

---

## 3. Custom Hook Extraction {#hook-extraction}

```tsx
// Template: extract local state + effects into a hook

// ❌ Before (inside component):
const [query, setQuery] = useState('');
const [results, setResults] = useState<SearchResult[]>([]);
const [isSearching, setIsSearching] = useState(false);

useEffect(() => {
  if (!query) { setResults([]); return; }
  setIsSearching(true);
  searchApi(query).then(r => {
    setResults(r);
    setIsSearching(false);
  });
}, [query]);

// ✅ After (hooks/useSearch.ts):
interface UseSearchReturn {
  query: string;
  results: SearchResult[];
  isSearching: boolean;
  setQuery: (q: string) => void;
}

export function useSearch(): UseSearchReturn {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (!query) { setResults([]); return; }
    let cancelled = false;                    // cleanup pattern
    setIsSearching(true);
    searchApi(query).then(r => {
      if (!cancelled) {
        setResults(r);
        setIsSearching(false);
      }
    });
    return () => { cancelled = true; };       // cancel on unmount / query change
  }, [query]);

  return { query, results, isSearching, setQuery };
}
```

---

## 4. Event Handler Typing {#events}

```tsx
// Input events
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
};

// Select
const handleSelect = (e: React.ChangeEvent<HTMLSelectElement>) => { ... };

// Textarea
const handleTextarea = (e: React.ChangeEvent<HTMLTextAreaElement>) => { ... };

// Form submit
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  // ...
};

// Keyboard
const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
  if (e.key === 'Enter') { ... }
};

// Mouse events
const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => { ... };

// Drag events
const handleDrop = (e: React.DragEvent<HTMLDivElement>) => { ... };

// Generic handler factory (reduces repetition)
const handleFieldChange =
  (field: keyof FormState) =>
  (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({ ...prev, [field]: e.target.value }));
  };
```

---

## 5. Context Typing {#context}

```tsx
// ✅ Typed context with a guard hook
interface UserContextValue {
  user: User | null;
  setUser: (user: User | null) => void;
}

const UserContext = React.createContext<UserContextValue | undefined>(undefined);

export function useUserContext(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUserContext must be used inside UserProvider');
  return ctx;
}

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
}
```

---

## 6. Performance Patterns {#performance}

```tsx
// useMemo: expensive computation
const sortedUsers = useMemo(
  () => [...users].sort((a, b) => a.name.localeCompare(b.name)),
  [users]
);

// useCallback: stable callback reference
const handleDelete = useCallback(
  (id: string) => dispatch(deleteUser(id)),
  [dispatch]
);

// React.memo: prevent re-render if props unchanged
interface UserRowProps {
  user: User;
  onDelete: (id: string) => void;
}
const UserRow = React.memo(function UserRow({ user, onDelete }: UserRowProps) {
  return <tr>...</tr>;
});

// React.lazy: code splitting
const HeavyChart = React.lazy(() => import('./HeavyChart'));
// Usage:
<Suspense fallback={<ChartSkeleton />}>
  {showChart && <HeavyChart data={data} />}
</Suspense>

// ❌ Common mistake: inline objects cause re-renders
<UserRow style={{ color: 'red' }} />      // new object every render
// ✅ Fix: extract or useMemo
const rowStyle = { color: 'red' } as const;  // constant — extract outside component
<UserRow style={rowStyle} />
```

---

## 7. Render Optimization {#render}

```tsx
// Early return pattern (reduces nesting)
export function UserProfile({ userId }: { userId: string }) {
  const { user, isLoading, error } = useUser(userId);

  if (isLoading) return <Skeleton />;           // guard clauses first
  if (error) return <Error message={error} />;
  if (!user) return <EmptyState />;

  return (                                       // clean main render
    <section>
      <UserHeader user={user} />
      <UserContent user={user} />
    </section>
  );
}

// Avoid conditional hooks (Rules of Hooks)
// ❌ Wrong:
if (isLoggedIn) {
  const data = useUserData(); // NEVER conditional
}

// ✅ Right: condition inside hook or after
const data = useUserData(); // always call
if (!isLoggedIn) return null; // guard after hooks
```

---

## 8. Testing Patterns {#testing}

```tsx
// Characterization test (before refactoring)
import { render, screen, fireEvent } from '@testing-library/react';

describe('UserCard', () => {
  const defaultProps = {
    user: { id: '1', name: 'Alice', email: 'alice@test.com' },
    onEdit: vi.fn(),
    onDelete: vi.fn(),
  };

  it('renders user name and email', () => {
    render(<UserCard {...defaultProps} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('alice@test.com')).toBeInTheDocument();
  });

  it('calls onEdit when edit button clicked', () => {
    render(<UserCard {...defaultProps} />);
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(defaultProps.onEdit).toHaveBeenCalledWith('1');
  });
});

// Hook testing with renderHook
import { renderHook, act } from '@testing-library/react';

it('useSearch returns filtered results', async () => {
  const { result } = renderHook(() => useSearch());
  act(() => result.current.setQuery('alice'));
  await waitFor(() => {
    expect(result.current.results.length).toBeGreaterThan(0);
  });
});
```
