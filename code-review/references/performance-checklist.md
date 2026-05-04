# Performance Checklist — React, NestJS & Express

Use this during Phase 6 of a full diff review, or whenever a change touches data fetching,
rendering, or server-side processing.

## Table of Contents
1. [React — Render & Bundle Performance](#react-perf)
2. [NestJS — Database & Server Performance](#nestjs-perf)
3. [Express — Request & Middleware Performance](#express-perf)
4. [Node.js Runtime — Universal Concerns](#nodejs-perf)
5. [Quick Performance Verdict](#verdict)

---

## 1. React — Render & Bundle Performance {#react-perf}

### 🔴 Critical

#### Unnecessary Re-Renders
```tsx
// ❌ New object reference on every parent render → child re-renders always
<UserCard config={{ theme: 'dark', size: 'lg' }} />

// ✅ Stable reference
const cardConfig = useMemo(() => ({ theme: 'dark', size: 'lg' }), []);
<UserCard config={cardConfig} />
```

```tsx
// ❌ Inline callback recreated every render
<Button onClick={() => handleClick(item.id)} />

// ✅ Memoized callback
const handleItemClick = useCallback(() => handleClick(item.id), [item.id, handleClick]);
<Button onClick={handleItemClick} />
```

#### Expensive Computation in Render Path
```tsx
// ❌ Sorted/filtered on every render
function ProductList({ products }) {
  const sorted = products.sort((a, b) => b.price - a.price); // runs every render
  return sorted.map(...);
}

// ✅ Memoized
const sorted = useMemo(() =>
  [...products].sort((a, b) => b.price - a.price),
[products]);
```

#### Context Triggering Whole-Tree Re-Renders
```tsx
// ❌ Single context with mixed concerns — any state change re-renders all consumers
const AppContext = createContext({ user, cart, theme, notifications });

// ✅ Split contexts — consumers only re-render when their slice changes
const UserContext = createContext(user);
const CartContext = createContext(cart);
```

### 🟡 Important

#### Missing Virtualization for Long Lists
```tsx
// ❌ Renders 10,000 DOM nodes
{products.map(p => <ProductCard key={p.id} {...p} />)}

// ✅ Only renders visible rows
import { FixedSizeList } from 'react-window';
<FixedSizeList height={600} itemCount={products.length} itemSize={80}>
  {({ index, style }) => <ProductCard style={style} {...products[index]} />}
</FixedSizeList>
```

#### No Code Splitting on Heavy Routes
```tsx
// ❌ Everything bundled into one chunk
import AdminDashboard from './AdminDashboard';

// ✅ Lazy-loaded — only downloads when user visits /admin
const AdminDashboard = React.lazy(() => import('./AdminDashboard'));
<Suspense fallback={<Spinner />}><AdminDashboard /></Suspense>
```

#### Bundle Size Red Flags
Check for these imports — they carry heavy payload:
- `import _ from 'lodash'` → use `import debounce from 'lodash/debounce'` (named import)
- `import * as d3 from 'd3'` → import only needed submodules
- `import { Button } from '@mui/material'` → check if tree shaking is configured
- Moment.js → replace with `date-fns` or `dayjs`
- Large icon libraries imported all at once

#### Images Not Optimized
```tsx
// ❌ No lazy loading, no explicit dimensions (causes layout shift)
<img src={hero} />

// ✅
<img src={hero} loading="lazy" width={1200} height={600} alt="Hero banner" />
```

### 🟢 Quality

- [ ] `React.memo` wrapping pure presentational components that receive stable props
- [ ] `useTransition` / `useDeferredValue` for non-urgent state updates (search, filters)
- [ ] Fonts preloaded with `<link rel="preload">` if added in this PR
- [ ] Web Vitals not regressed: LCP, CLS, INP — check if the change affects initial paint

---

## 2. NestJS — Database & Server Performance {#nestjs-perf}

### 🔴 Critical

#### N+1 Query (most common DB performance bug)
```typescript
// ❌ 1 query for orders + N queries for users (one per order)
const orders = await orderRepo.find();
for (const order of orders) {
  order.user = await userRepo.findOne({ where: { id: order.userId } }); // N queries!
}

// ✅ Single JOIN query
const orders = await orderRepo.find({ relations: ['user'] });
// or QueryBuilder for complex cases:
const orders = await orderRepo
  .createQueryBuilder('order')
  .leftJoinAndSelect('order.user', 'user')
  .getMany();
```

#### Unbounded List Queries
```typescript
// ❌ SELECT * with no LIMIT — could return millions of rows
const users = await userRepo.find();

// ✅ Always paginate
const [users, total] = await userRepo.findAndCount({
  take: dto.limit ?? 20,
  skip: ((dto.page ?? 1) - 1) * (dto.limit ?? 20),
  order: { createdAt: 'DESC' },
});
```

#### Selecting All Columns When You Need Two
```typescript
// ❌ Fetches every column including large BLOBs
const users = await userRepo.find();

// ✅ Select only what you need
const users = await userRepo.find({
  select: { id: true, email: true, displayName: true },
});
```

### 🟡 Important

#### Missing Index on Frequently Queried Columns
```typescript
// If a new query filters/orders by a column, add an index:
@Entity()
export class Order {
  @Index() // ← add when this column is used in WHERE or ORDER BY
  @Column()
  status: OrderStatus;

  @Index()
  @Column()
  userId: string;
}
```

#### No Caching on Expensive Read-Heavy Endpoints
```typescript
// ❌ DB hit on every request for relatively static data
@Get('config/feature-flags')
async getFlags() { return this.configService.getAllFlags(); }

// ✅ Cache with TTL
@CacheKey('feature-flags')
@CacheTTL(60) // seconds
@UseInterceptors(CacheInterceptor)
@Get('config/feature-flags')
async getFlags() { return this.configService.getAllFlags(); }
```

#### Synchronous CPU Work Blocking the Event Loop
```typescript
// ❌ JSON.parse of a 10MB payload blocks all other requests
@Post('import')
async importData(@Body() body: any) {
  const parsed = JSON.parse(body.largeJson); // blocks!
  ...
}

// ✅ Offload to worker thread or stream
import { Worker } from 'worker_threads';
```

#### TypeORM Lazy Relations (Hidden N+1)
```typescript
// ❌ @RelationId with lazy loading triggers a query on each access
@OneToMany(() => Order, order => order.user, { lazy: true })
orders: Promise<Order[]>;

// Accessing user.orders inside a loop = N+1 in disguise
// ✅ Always eager-load with explicit relations when iterating
```

### 🟢 Quality

- [ ] Long-running jobs use Bull/BullMQ queue, not blocking the request lifecycle
- [ ] DB connection pool size tuned for expected concurrency
- [ ] `EXPLAIN ANALYZE` run on new complex queries (not enforced in code review, but worth noting)
- [ ] Response compression enabled (`compression` middleware or NestJS `CompressInterceptor`)

---

## 3. Express — Request & Middleware Performance {#express-perf}

### 🔴 Critical

#### Synchronous File System Calls in Request Handlers
```typescript
// ❌ fs.readFileSync blocks the entire Node process
app.get('/config', (req, res) => {
  const config = fs.readFileSync('./config.json', 'utf8'); // blocks!
  res.json(JSON.parse(config));
});

// ✅ Async
app.get('/config', async (req, res) => {
  const config = await fs.promises.readFile('./config.json', 'utf8');
  res.json(JSON.parse(config));
});
```

#### No Response Compression
```typescript
// ❌ Sending large JSON/HTML uncompressed
app.use(express.json());

// ✅ Add compression early in the middleware stack
import compression from 'compression';
app.use(compression());
```

#### Missing Database Query Projection
```typescript
// ❌ Mongoose — fetches all fields including large ones
const users = await User.find({ active: true });

// ✅ Project only what you need
const users = await User.find({ active: true }).select('name email avatar');
```

### 🟡 Important

- [ ] Mongoose `.populate()` not used in loops (N+1 risk — use aggregation pipeline instead)
- [ ] `JSON.parse` / `JSON.stringify` on very large objects not in hot paths
- [ ] Static files served via CDN/nginx in production — not Express `express.static`
- [ ] Response streaming used for large payloads instead of buffering entire response

### 🟢 Quality

- [ ] `keep-alive` connections configured for upstream DB/API calls
- [ ] HTTP/2 considered if serving API + assets from same origin

---

## 4. Node.js Runtime — Universal Concerns {#nodejs-perf}

### Event Loop Blockers (apply to both NestJS and Express)
```typescript
// ❌ These block ALL requests while running:
const hash = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512'); // sync!
const result = JSON.parse(hugeMegabyteString); // blocks for large payloads
const sorted = massiveArray.sort(compareFn); // can block for large arrays

// ✅ Use async versions:
const hash = await new Promise((resolve, reject) =>
  crypto.pbkdf2(password, salt, 100000, 64, 'sha512', (err, key) =>
    err ? reject(err) : resolve(key)
  )
);
```

### Memory Leak Signals
- [ ] Event listeners added but never removed (especially in long-lived services)
- [ ] Large arrays/objects accumulated in module-level variables
- [ ] Streams not properly destroyed/closed after use
- [ ] `setInterval` without `clearInterval` in cleanup

### Async/Concurrency
```typescript
// ❌ Sequential awaits when operations are independent
const user = await getUser(id);
const orders = await getOrders(id); // waits for getUser to finish first
const prefs = await getPrefs(id);   // waits for getOrders to finish

// ✅ Parallel — 3x faster
const [user, orders, prefs] = await Promise.all([
  getUser(id),
  getOrders(id),
  getPrefs(id),
]);
```

---

## 5. Quick Performance Verdict {#verdict}

| Finding | Severity | Action |
|---------|----------|--------|
| N+1 query in endpoint | CRITICAL | Block — fix before merge |
| Unbounded DB query (no limit) | CRITICAL | Block — fix before merge |
| Sync file I/O in request handler | CRITICAL | Block — fix before merge |
| Event loop blocker (sync crypto, sort on huge array) | HIGH | Fix before merge |
| Missing pagination on list endpoint | HIGH | Fix before merge |
| Sequential awaits (should be Promise.all) | MEDIUM | Fix before merge |
| No code splitting on heavy page | MEDIUM | Fix before merge |
| Long list without virtualization | MEDIUM | Fix before merge |
| lodash full import | LOW | Suggestion |
| Missing response compression | LOW | Suggestion |
| No cache on expensive read endpoint | LOW | Suggestion |
