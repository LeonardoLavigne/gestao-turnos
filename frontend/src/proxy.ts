import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 1. Specify protected and public routes
const protectedRoutes = ['/dashboard', '/turnos'];
const publicRoutes = ['/login'];

export default function proxy(request: NextRequest) {
    // Check for the auth_token cookie
    const token = request.cookies.get('auth_token')?.value;
    const { pathname } = request.nextUrl;

    // Helper to check if the current path matches any protected route
    const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
    const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));

    // 2. Redirect to /login if the user is not authenticated and tries to access a protected route
    if (isProtectedRoute && !token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    // 3. Redirect to /dashboard if the user is authenticated and tries to access a public route (like login)
    if (isPublicRoute && token) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
    }

    // If token exists (or route is not protected), proceed.
    return NextResponse.next();
}

// Configure which paths the middleware should run on
export const config = {
    // Matcher excluding API, static files, and images to improve performance
    matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
