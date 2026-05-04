# NestJS Patterns — Deep Reference

## Table of Contents
1. [Security Patterns](#security)
2. [Validation & DTOs](#validation)
3. [Dependency Injection](#di)
4. [Database & TypeORM](#database)
5. [Guards & Auth](#guards)
6. [Exception Handling](#exceptions)
7. [Module Architecture](#modules)

---

## 1. Security Patterns {#security}

### ❌ Unprotected routes
```typescript
// WRONG — no guard, any request goes through
@Get('admin/users')
getAllUsers() { ... }

// ✅ CORRECT
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles(Role.ADMIN)
@Get('admin/users')
getAllUsers() { ... }
```

### ❌ Missing whitelist on ValidationPipe
```typescript
// WRONG — unknown properties passed through to service
app.useGlobalPipes(new ValidationPipe());

// ✅ CORRECT — strip unknown fields, reject invalid
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,            // strip unknown properties
  forbidNonWhitelisted: true, // throw on unknown properties
  transform: true,            // auto-transform to DTO types
}));
```

### ❌ Raw body used without validation
```typescript
// WRONG
@Post()
create(@Body() body: any) { return this.service.create(body); }

// ✅ CORRECT — DTO with class-validator
@Post()
create(@Body() dto: CreateUserDto) { return this.service.create(dto); }
```

---

## 2. Validation & DTOs {#validation}

### DTO Best Practices
```typescript
import { IsEmail, IsString, MinLength, IsOptional, IsEnum } from 'class-validator';
import { Transform, Type } from 'class-transformer';

export class CreateUserDto {
  @IsEmail()
  @Transform(({ value }) => value?.toLowerCase().trim()) // normalize
  email: string;

  @IsString()
  @MinLength(8)
  password: string;

  @IsEnum(Role)
  @IsOptional()
  role?: Role = Role.USER; // safe default

  @Type(() => Number) // transform query param string to number
  @IsOptional()
  age?: number;
}
```

### ❌ Exposing internal entity fields
```typescript
// WRONG — password hash returned to client
@Get(':id')
async getUser(@Param('id') id: string): Promise<User> {
  return this.userService.findById(id); // returns full entity
}

// ✅ CORRECT — use @Exclude() on entity or dedicated response DTO
export class UserResponseDto {
  @Expose() id: string;
  @Expose() email: string;
  // password not included
}

@Get(':id')
@SerializeOptions({ type: UserResponseDto })
async getUser(@Param('id') id: string): Promise<UserResponseDto> {
  return plainToInstance(UserResponseDto, await this.userService.findById(id), {
    excludeExtraneousValues: true,
  });
}
```

---

## 3. Dependency Injection {#di}

### ❌ Creating services manually (breaks DI)
```typescript
// WRONG
constructor() {
  this.emailService = new EmailService(); // not injectable, not mockable
}

// ✅ CORRECT — let NestJS inject
constructor(private readonly emailService: EmailService) {}
```

### ❌ Circular dependency without forwardRef
```typescript
// If UserService depends on AuthService and vice versa:
// WRONG — will throw "Cannot read property of undefined"
@Injectable()
class UserService {
  constructor(private authService: AuthService) {}
}

// ✅ — use forwardRef (but also consider refactoring to break the cycle)
@Injectable()
class UserService {
  constructor(
    @Inject(forwardRef(() => AuthService))
    private authService: AuthService,
  ) {}
}
```

### ❌ Using process.env directly in services
```typescript
// WRONG — not testable, not validated
const apiKey = process.env.API_KEY;

// ✅ CORRECT — inject ConfigService
constructor(private configService: ConfigService) {}

const apiKey = this.configService.get<string>('API_KEY');
```

---

## 4. Database & TypeORM {#database}

### ❌ N+1 query problem
```typescript
// WRONG — 1 query for users + N queries for their orders
const users = await userRepo.find();
for (const user of users) {
  user.orders = await orderRepo.findBy({ userId: user.id }); // N queries!
}

// ✅ CORRECT — eager join
const users = await userRepo.find({ relations: ['orders'] });
// or QueryBuilder:
const users = await userRepo
  .createQueryBuilder('user')
  .leftJoinAndSelect('user.orders', 'order')
  .getMany();
```

### ❌ Missing transactions for multi-step writes
```typescript
// WRONG — partial failure leaves inconsistent data
await userRepo.save(user);
await walletRepo.save(wallet); // if this fails, user exists without wallet

// ✅ CORRECT
await dataSource.transaction(async (manager) => {
  await manager.save(User, user);
  await manager.save(Wallet, wallet);
});
```

### ❌ Unbounded queries in list endpoints
```typescript
// WRONG — returns all records
@Get()
findAll() { return this.userRepo.find(); }

// ✅ CORRECT — always paginate
@Get()
findAll(@Query() paginationDto: PaginationDto) {
  return this.userRepo.findAndCount({
    take: paginationDto.limit ?? 20,
    skip: (paginationDto.page - 1) * (paginationDto.limit ?? 20),
  });
}
```

---

## 5. Guards & Auth {#guards}

### ❌ JWT not verified on every request
```typescript
// WRONG — strategy extracted from token without verifying signature
// Always use passport-jwt with secretOrKey configured

// ✅ CORRECT — JwtStrategy validates every token
@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(configService: ConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false, // never set to true in prod
      secretOrKey: configService.get('JWT_SECRET'),
    });
  }
  async validate(payload: JwtPayload) {
    return { userId: payload.sub, email: payload.email, role: payload.role };
  }
}
```

### ❌ Role check in service (bypass risk)
```typescript
// WRONG — any caller that skips the route can call service directly
async deleteUser(requesterId: string, targetId: string) {
  if (requester.role !== 'admin') throw new ForbiddenException();
}

// ✅ CORRECT — enforce at controller/guard level + service is secondary defense
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles(Role.ADMIN)
@Delete(':id')
async deleteUser(@Param('id') id: string) { ... }
```

---

## 6. Exception Handling {#exceptions}

### ❌ Throwing generic Error in NestJS context
```typescript
// WRONG — becomes 500, no helpful message
throw new Error('User not found');

// ✅ CORRECT — HTTP exceptions with status codes
throw new NotFoundException(`User ${id} not found`);
throw new BadRequestException('Invalid email format');
throw new ForbiddenException('Insufficient permissions');
throw new ConflictException('Email already in use');
```

### ❌ No global exception filter
```typescript
// WRONG — unhandled exceptions expose stack traces
// ✅ Set up a global exception filter in main.ts:
app.useGlobalFilters(new AllExceptionsFilter(logger));

// AllExceptionsFilter:
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const status = exception instanceof HttpException
      ? exception.getStatus()
      : HttpStatus.INTERNAL_SERVER_ERROR;

    this.logger.error(exception);
    ctx.getResponse().status(status).json({
      statusCode: status,
      message: exception instanceof HttpException
        ? exception.message
        : 'Internal server error',
    });
  }
}
```

---

## 7. Module Architecture {#modules}

### ❌ Importing cross-module without explicit export
```typescript
// WRONG — UserModule uses AuthService from AuthModule
// But AuthModule doesn't export it → undefined at runtime

// ✅ CORRECT — explicitly export from provider module
@Module({
  providers: [AuthService],
  exports: [AuthService], // ← required for other modules to use it
})
export class AuthModule {}
```

### ❌ Everything in one module
```typescript
// WRONG — AppModule with 20+ providers is a God Module
// ✅ CORRECT — feature modules with clear boundaries
// auth/, users/, orders/, notifications/ — each a NestJS module
```
