<script lang="ts">
	import { fade, fly } from 'svelte/transition';
	import { onMount } from 'svelte';
    import { signIn, api } from '$lib/api';

    // State for flip
    let isFlipped = $state(false);
    
    // Login State
    let loginEmail = $state('');
    let loginPassword = $state('');
    let loginError = $state('');
    let loginBusy = $state(false);

    // Register State
    let regName = $state('');
    let regEmail = $state('');
    let regInstitution = $state('');
    let regPassword = $state('');
    let regConfirm = $state('');
    let regError = $state('');
    let regBusy = $state(false);

    let visible = $state(false);
    // Vite removes DEV in production builds; the optional demo mode is explicit.
    const quickLoginEnabled = import.meta.env.DEV || import.meta.env.MODE === 'demo';
    const demoAccounts = {
        student: { label: 'Student', email: import.meta.env.VITE_DEMO_STUDENT_EMAIL || 'student@test.com', password: import.meta.env.VITE_DEMO_STUDENT_PASSWORD || 'Student@123' },
        manager: { label: 'Admission / Marketing Manager', email: import.meta.env.VITE_DEMO_MANAGER_EMAIL || 'manager@test.com', password: import.meta.env.VITE_DEMO_MANAGER_PASSWORD || 'Manager@123' },
        admin: { label: 'Admin', email: import.meta.env.VITE_DEMO_ADMIN_EMAIL || 'admin@test.com', password: import.meta.env.VITE_DEMO_ADMIN_PASSWORD || 'Admin@123' }
    };
    function fillDemo(role: keyof typeof demoAccounts) { const account = demoAccounts[role]; loginEmail = account.email; loginPassword = account.password; loginError = ''; }
	onMount(() => { visible = true; if (quickLoginEnabled) fillDemo('student'); });

    async function handleLogin(event: SubmitEvent) {
        event.preventDefault(); loginBusy = true; loginError = '';
        try { await signIn(loginEmail, loginPassword); }
        catch (e) { loginError = (e as Error).message; }
        finally { loginBusy = false; }
    }

    async function handleRegister(event: SubmitEvent) {
        event.preventDefault(); regBusy = true; regError = '';
        if (regPassword !== regConfirm) {
            regError = "Passwords do not match.";
            regBusy = false;
            return;
        }
        const role = regInstitution.trim() ? 'admission_manager' : 'student';
        try { 
            await api('/auth/register', { 
                method: 'POST', 
                body: JSON.stringify({name: regName, email: regEmail, password: regPassword, role, institution: regInstitution.trim()}) 
            }); 
            // After register, automatically log in
            await signIn(regEmail, regPassword); 
        }
        catch(e) { regError = (e as Error).message; } 
        finally { regBusy = false; }
    }

    function flipToRegister() {
        isFlipped = true;
    }

    function flipToLogin() {
        isFlipped = false;
    }
</script>

<svelte:head>
	<title>DecisionIntel | Authentication</title>
</svelte:head>

<style>
    /* CSS for 3D Flip */
    .perspective-container {
        perspective: 1500px;
    }
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        transition: transform 0.8s cubic-bezier(0.4, 0.0, 0.2, 1);
        transform-style: preserve-3d;
    }
    .flip-card-inner.flipped {
        transform: rotateY(-180deg);
    }
    .flip-card-face {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }
    .flip-card-back {
        transform: rotateY(180deg);
    }
</style>

<div class="min-h-screen flex items-center justify-center relative bg-primary overflow-hidden p-4 sm:p-8">
    <!-- Background aesthetics -->
    <div class="absolute top-0 right-0 w-150 h-150 bg-accent/10 rounded-full blur-[120px] pointer-events-none"></div>
    <div class="absolute bottom-0 left-0 w-125 h-125 bg-secondary/10 rounded-full blur-[100px] pointer-events-none"></div>
    <!-- Subtle campus blur background behind everything -->
    <div class="absolute inset-0 bg-[url('/graph_analytics.jpg')] bg-cover bg-center opacity-5 blur-xl pointer-events-none"></div>

    {#if visible}
    <div class="perspective-container w-full max-w-5xl h-187.5 md:h-162.5 z-10" in:fly={{ y: 30, duration: 1000, delay: 200 }}>
        <div class="flip-card-inner {isFlipped ? 'flipped' : ''}">
            
            <!-- FRONT FACE (LOGIN) -->
            <div class="flip-card-face flex flex-col md:flex-row bg-white/3 backdrop-blur-2xl border border-white/10 shadow-[0_15px_40px_rgba(0,0,0,0.6)] rounded-3xl overflow-hidden">
                <!-- LEFT BRANDING (Login) -->
                <div class="hidden md:flex w-1/2 relative flex-col justify-between p-12 overflow-hidden bg-black/30 border-r border-white/5">
                    <img src="/rl_optimization.jpg" alt="AI Education" class="absolute inset-0 w-full h-full object-cover opacity-10 mix-blend-overlay">
                    <div class="absolute inset-0 bg-linear-to-br from-primary/90 to-transparent"></div>
                    <div class="absolute bottom-0 left-0 w-full h-1/2 bg-linear-to-t from-primary to-transparent"></div>
                    
                    <div class="relative z-10 flex items-center gap-3">
                        <div class="w-10 h-10 rounded-xl bg-linear-to-br from-accent to-secondary flex items-center justify-center shadow-lg">
                            <span class="text-white text-xl">🎓</span>
                        </div>
                        <a href="/" class="text-2xl font-bold tracking-wider text-white hover:text-accent transition-colors">Decision<span class="text-accent font-serif italic">Intel</span></a>
                    </div>

                    <div class="relative z-10 mb-6">
                        <h2 class="text-3xl lg:text-4xl font-bold text-white mb-4 leading-tight">Smarter Admissions.<br><span class="text-accent font-serif italic">Better Decisions.</span></h2>
                        <p class="text-text-secondary text-base mb-8 leading-relaxed">AI-powered intelligence for student admission decisions and marketing optimization.</p>
                        
                        <div class="space-y-3">
                            <div class="flex items-center gap-3 bg-white/5 p-3 rounded-2xl border border-white/5 backdrop-blur-sm shadow-sm transition-transform hover:translate-x-2">
                                <div class="w-8 h-8 rounded-full bg-secondary/30 flex items-center justify-center text-white border border-secondary/50 text-sm">🎯</div>
                                <span class="text-white font-medium text-sm">Predict Admissions</span>
                            </div>
                            <div class="flex items-center gap-3 bg-white/5 p-3 rounded-2xl border border-white/5 backdrop-blur-sm shadow-sm transition-transform hover:translate-x-2">
                                <div class="w-8 h-8 rounded-full bg-accent/30 flex items-center justify-center text-white border border-accent/50 text-sm">🔍</div>
                                <span class="text-white font-medium text-sm">Understand Student Leads</span>
                            </div>
                            <div class="flex items-center gap-3 bg-white/5 p-3 rounded-2xl border border-white/5 backdrop-blur-sm shadow-sm transition-transform hover:translate-x-2">
                                <div class="w-8 h-8 rounded-full bg-cta/20 flex items-center justify-center text-cta border border-cta/30 text-sm">💰</div>
                                <span class="text-white font-medium text-sm">Optimize Marketing Budget</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- RIGHT FORM (Login) -->
                <div class="w-full md:w-1/2 flex flex-col justify-center p-8 sm:p-12 lg:p-16 relative bg-white/1">
                    
                    <!-- Mobile Logo -->
                    <div class="md:hidden flex items-center gap-2 mb-8 self-center">
                        <div class="w-8 h-8 rounded-lg bg-linear-to-br from-accent to-secondary flex items-center justify-center">
                            <span class="text-white text-sm">🎓</span>
                        </div>
                        <span class="text-xl font-bold tracking-wider text-white">Decision<span class="text-accent font-serif italic">Intel</span></span>
                    </div>

                    <div class="text-center md:text-left mb-10">
                        <h3 class="text-3xl font-bold text-white mb-2">Welcome Back</h3>
                        <p class="text-text-secondary">Sign in to continue to Decision-Intel.</p>
                    </div>

                    {#if loginError}<p role="alert" class="text-red-400 mb-6 text-sm bg-red-400/10 p-3 rounded-lg border border-red-400/20">{loginError}</p>{/if}
                    
                    <form class="flex flex-col gap-6 w-full" onsubmit={handleLogin}>
                        <div class="flex flex-col gap-2">
                            <label for="login-email" class="text-sm font-medium text-text-secondary">Email Address</label>
                            <input type="email" id="login-email" bind:value={loginEmail} placeholder="name@institution.edu" required class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent transition-all shadow-inner" />
                        </div>
                        <div class="flex flex-col gap-2">
                            <div class="flex justify-between items-center">
                                <label for="login-password" class="text-sm font-medium text-text-secondary">Password</label>
                                <a href="/forgot-password" class="text-xs text-accent hover:text-white transition-colors">Forgot Password?</a>
                            </div>
                            <input type="password" id="login-password" bind:value={loginPassword} placeholder="••••••••" required class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent transition-all shadow-inner" />
                        </div>
                        {#if quickLoginEnabled}
                            <div class="rounded-xl border border-white/10 bg-white/2.5 p-3">
                                <p class="text-[10px] uppercase tracking-[.14em] text-slate-400 font-bold mb-2">Development quick login</p>
                                <div class="flex flex-wrap gap-2">{#each Object.entries(demoAccounts) as [role, account]}<button type="button" onclick={() => fillDemo(role as keyof typeof demoAccounts)} class="text-xs px-2.5 py-1.5 rounded-lg border border-white/10 text-text-secondary hover:text-white hover:border-accent/50 hover:bg-accent/10 transition-colors">{account.label}</button>{/each}</div>
                            </div>
                        {/if}

                        <button type="submit" disabled={loginBusy} class="w-full bg-cta hover:bg-cta/90 text-card font-bold text-lg rounded-xl py-3.5 mt-2 transition-all shadow-[0_0_20px_rgba(242,166,43,0.2)] hover:shadow-[0_0_30px_rgba(242,166,43,0.4)] transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:hover:translate-y-0">
                            {loginBusy ? 'Signing in...' : 'Sign In'}
                        </button>

                        <div class="mt-6 text-center text-sm">
                            <span class="text-text-secondary">Don't have an account?</span>
                            <button type="button" onclick={flipToRegister} class="ml-1 text-accent hover:text-white font-medium transition-colors focus:outline-none group">
                                Create Account <span class="inline-block transition-transform group-hover:translate-x-1">→</span>
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- BACK FACE (REGISTER) -->
            <!-- Flex-row means left form, right branding visually when physical back face is viewed -->
            <div class="flip-card-face flip-card-back flex flex-col md:flex-row bg-white/3 backdrop-blur-2xl border border-white/10 shadow-[0_15px_40px_rgba(0,0,0,0.6)] rounded-3xl overflow-hidden">
                
                <!-- LEFT FORM (Register) - Visually on the left when flipped -->
                <div class="w-full md:w-[55%] flex flex-col justify-center p-6 sm:p-8 lg:p-12 relative bg-white/1">
                    
                    <!-- Mobile Logo -->
                    <div class="md:hidden flex items-center gap-2 mb-6 self-center">
                        <div class="w-8 h-8 rounded-lg bg-linear-to-br from-accent to-secondary flex items-center justify-center">
                            <span class="text-white text-sm">🎓</span>
                        </div>
                        <span class="text-xl font-bold tracking-wider text-white">Decision<span class="text-accent font-serif italic">Intel</span></span>
                    </div>

                    <div class="text-center md:text-left mb-6">
                        <h3 class="text-3xl font-bold text-white mb-2">Create Account</h3>
                        <p class="text-text-secondary text-sm">Register as a student or admission/marketing manager.</p>
                    </div>

                    {#if regError}<p role="alert" class="text-red-400 mb-4 text-sm bg-red-400/10 p-3 rounded-lg border border-red-400/20">{regError}</p>{/if}
                    
                    <form class="flex flex-col gap-4 w-full" onsubmit={handleRegister}>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div class="flex flex-col gap-1.5">
                                <label for="reg-name" class="text-xs font-medium text-text-secondary">Full Name</label>
                                <input type="text" id="reg-name" bind:value={regName} placeholder="Jane Doe" required class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent transition-all text-sm shadow-inner" />
                            </div>
                            <div class="flex flex-col gap-1.5">
                                <label for="reg-email" class="text-xs font-medium text-text-secondary">Email Address</label>
                                <input type="email" id="reg-email" bind:value={regEmail} placeholder="jane@institution.edu" required class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent transition-all text-sm shadow-inner" />
                            </div>
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <label for="reg-institution" class="text-xs font-medium text-text-secondary">Institution Name <span class="text-slate-500">(optional)</span></label>
                            <input type="text" id="reg-institution" bind:value={regInstitution} placeholder="Tech University" class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent transition-all text-sm shadow-inner" />
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div class="flex flex-col gap-1.5">
                                <label for="reg-pass" class="text-xs font-medium text-text-secondary">Password</label>
                                <input type="password" id="reg-pass" bind:value={regPassword} placeholder="••••••••" required minlength="12" class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent transition-all text-sm shadow-inner" />
                            </div>
                            <div class="flex flex-col gap-1.5">
                                <label for="reg-confirm" class="text-xs font-medium text-text-secondary">Confirm Password</label>
                                <input type="password" id="reg-confirm" bind:value={regConfirm} placeholder="••••••••" required class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent transition-all text-sm shadow-inner" />
                            </div>
                        </div>

                        <button type="submit" disabled={regBusy} class="w-full bg-accent hover:bg-accent/90 text-white font-bold rounded-xl py-3.5 mt-2 transition-all shadow-[0_0_20px_rgba(164,123,224,0.3)] hover:shadow-[0_0_30px_rgba(164,123,224,0.5)] transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70 disabled:hover:translate-y-0">
                            {regBusy ? 'Creating Account...' : 'Create Account'}
                        </button>

                        <div class="mt-4 text-center text-sm">
                            <span class="text-text-secondary">Already have an account?</span>
                            <button type="button" onclick={flipToLogin} class="ml-1 text-cta hover:text-white font-medium transition-colors focus:outline-none group">
                                <span class="inline-block transition-transform group-hover:-translate-x-1">←</span> Sign In
                            </button>
                        </div>
                    </form>
                </div>

                <!-- RIGHT BRANDING (Register) - Visually on the right when flipped -->
                <div class="hidden md:flex w-[45%] relative flex-col justify-center items-center p-12 overflow-hidden bg-black/30 border-l border-white/5">
                    <img src="/graph_analytics.jpg" alt="Analytics" class="absolute inset-0 w-full h-full object-cover opacity-10 mix-blend-overlay">
                    <div class="absolute inset-0 bg-linear-to-bl from-primary/90 to-transparent"></div>
                    <div class="absolute top-0 right-0 w-full h-1/2 bg-linear-to-b from-primary to-transparent"></div>
                    
                    <div class="relative z-10 text-center">
                        <div class="w-20 h-20 mx-auto rounded-3xl bg-white/5 flex items-center justify-center border border-white/10 shadow-[0_0_30px_rgba(255,255,255,0.05)] backdrop-blur-md mb-8">
                            <span class="text-4xl text-accent">🚀</span>
                        </div>
                        <h3 class="text-2xl font-bold text-white mb-4">Join the future of admissions</h3>
                            <p class="text-text-secondary leading-relaxed max-w-sm mx-auto">
                                Create an account to submit and track your admission enquiry as a student, or manage admission leads and marketing as an institution.
                            </p>
                    </div>
                </div>

            </div>
        </div>
    </div>
    {/if}
</div>
