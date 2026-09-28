<script lang="ts">
    import { tick, untrack } from 'svelte';
    import { signIn, api } from '$lib/api';
    import OutlineIcon from './OutlineIcon.svelte';
import ThemeToggle from '$lib/ThemeToggle.svelte';

    let { face = 'login' }: { face?: 'login' | 'register' } = $props();

    type Errors = Record<string, string>;

    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    const STATES = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Delhi', 'Goa', 'Gujarat',
        'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra',
        'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim',
        'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
    ];

    const GENDERS = [
        { value: 'female', label: 'Female' },
        { value: 'male', label: 'Male' },
        { value: 'other', label: 'Other' },
        { value: 'prefer_not_to_say', label: 'Prefer not to say' }
    ];

    const QUALIFICATIONS = [
        'Secondary (10th)', 'Higher Secondary (12th)', 'Undergraduate', 'Postgraduate', 'Doctorate', 'Other'
    ];

    const YEARS = Array.from({ length: 20 }, (_, i) => String(new Date().getFullYear() + 1 - i));

    // Order matters: it drives validation order and first-error scrolling.
    const REGISTER_FIELDS = [
        'name', 'date_of_birth', 'gender', 'email', 'mobile',
        'door_no', 'street', 'area', 'city', 'district', 'state', 'pincode',
        'qualification', 'institution', 'completion_year', 'course_interested',
        'password', 'confirm_password'
    ] as const;

    // Which face the card opens on is a one-time choice from the route; the
    // in-card Login/Register switch owns the state from then on.
    let flipped = $state(untrack(() => face === 'register'));

    let email = $state('');
    let password = $state('');
    let loginError = $state('');
    let loginBusy = $state(false);
    let loginRevealed = $state(false);

    let regError = $state('');
    let regBusy = $state(false);
    let regRevealed = $state(false);
    let regErrors = $state<Errors>({});
    let regDone = $state('');

    let form = $state({
        name: '', date_of_birth: '', gender: '',
        email: '', mobile: '',
        door_no: '', street: '', area: '', city: '', district: '', state: '', pincode: '',
        qualification: '', institution: '', completion_year: '', course_interested: '',
        password: '', confirm_password: ''
    });

    function value(key: string): string {
        return (form as unknown as Record<string, string>)[key] ?? '';
    }

    function setValue(key: string, next: string) {
        (form as unknown as Record<string, string>)[key] = next;
        if (regErrors[key]) {
            const { [key]: _removed, ...rest } = regErrors;
            regErrors = rest;
        }
    }

    function validateRegister(): Errors {
        const found: Errors = {};
        const require_ = (key: string, message: string) => {
            if (!value(key).trim()) found[key] = message;
        };

        require_('name', 'Enter your full name');
        if (!value('date_of_birth')) found.date_of_birth = 'Select your date of birth';
        else {
            const dob = new Date(value('date_of_birth'));
            if (Number.isNaN(dob.getTime()) || dob >= new Date()) found.date_of_birth = 'Date of birth must be in the past';
            else if ((Date.now() - dob.getTime()) / 31557600000 < 10) found.date_of_birth = 'You must be at least 10 years old';
        }
        if (!value('gender')) found.gender = 'Select a gender';

        if (!value('email').trim()) found.email = 'Enter your email address';
        else if (!EMAIL_RE.test(value('email').trim())) found.email = 'Enter a valid email address';

        if (!value('mobile').trim()) found.mobile = 'Enter your mobile number';
        else if (!/^\d{10}$/.test(value('mobile').replace(/\D/g, ''))) found.mobile = 'Enter a 10 digit mobile number';

        for (const key of ['door_no', 'street', 'area', 'city', 'district', 'state']) {
            require_(key, 'This field is required');
        }
        if (!value('pincode').trim()) found.pincode = 'Enter your PIN code';
        else if (!/^\d{6}$/.test(value('pincode').trim())) found.pincode = 'Enter a valid 6 digit PIN code';

        if (!value('qualification')) found.qualification = 'Select your highest qualification';
        require_('institution', 'Enter your institution name');
        if (!value('completion_year')) found.completion_year = 'Select the year you completed it';
        else {
            const year = Number(value('completion_year'));
            if (year < 1950 || year > new Date().getFullYear() + 1) found.completion_year = 'Enter a realistic completion year';
        }
        require_('course_interested', 'Enter the course you are interested in');

        if (!value('password')) found.password = 'Create a password';
        else if (value('password').length < 12) found.password = 'Use at least 12 characters';
        if (!value('confirm_password')) found.confirm_password = 'Re-enter your password';
        else if (value('confirm_password') !== value('password')) found.confirm_password = 'Passwords do not match';

        return found;
    }

    async function scrollToError(key: string) {
        await tick();
        const el = document.getElementById(`reg-${key}`);
        el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        (el as HTMLElement | null)?.focus?.({ preventScroll: true });
    }

    function showRegister() {
        flipped = true;
        regError = '';
        tick().then(() => document.getElementById('reg-name')?.focus());
    }

    function showLogin() {
        flipped = false;
        regError = '';
        tick().then(() => document.getElementById('email')?.focus());
    }

    async function submitLogin(event: SubmitEvent) {
        event.preventDefault();
        if (loginBusy) return;
        loginError = '';
        if (!EMAIL_RE.test(email.trim())) {
            loginError = 'Enter a valid email address.';
            return;
        }
        loginBusy = true;
        try {
            await signIn(email.trim(), password);
        } catch (e) {
            loginError = (e as Error).message;
        } finally {
            loginBusy = false;
        }
    }

    async function submitRegister(event: SubmitEvent) {
        event.preventDefault();
        if (regBusy) return;
        regError = '';

        const found = validateRegister();
        regErrors = found;
        const first = REGISTER_FIELDS.find((key) => found[key]);
        if (first) {
            regError = 'Some details still need your attention.';
            await scrollToError(first);
            return;
        }

        regBusy = true;
        try {
            const user = await api('/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    name: value('name').trim(),
                    email: value('email').trim().toLowerCase(),
                    password: value('password'),
                    date_of_birth: value('date_of_birth'),
                    gender: value('gender'),
                    mobile: value('mobile').replace(/\D/g, ''),
                    door_no: value('door_no').trim(),
                    street: value('street').trim(),
                    area: value('area').trim(),
                    city: value('city').trim(),
                    district: value('district').trim(),
                    state: value('state'),
                    pincode: value('pincode').trim(),
                    qualification: value('qualification'),
                    institution: value('institution').trim(),
                    completion_year: Number(value('completion_year')),
                    course_interested: value('course_interested').trim()
                })
            });
            regDone = user?.email ?? value('email').trim().toLowerCase();
            email = regDone;
            password = '';
        } catch (e) {
            regError = (e as Error).message;
        } finally {
            regBusy = false;
        }
    }
</script>

<div class="auth">
    <div class="glow glow-a" aria-hidden="true"></div>
    <div class="glow glow-b" aria-hidden="true"></div>

    <a class="back" href="/">
        <OutlineIcon name="chevron-right" size={16} />
        Back to home
    </a>

    <div class="auth-theme">
        <ThemeToggle />
    </div>

    <div class="stage">
        <div class="flip" class:flipped>
            <!-- ======================= FRONT FACE : LOGIN ======================= -->
            <section class="face front" inert={flipped} aria-hidden={flipped} aria-label="Sign in">
                <div class="brand-pane">
                    <div class="brand">
                        <span class="di-brand-mark"><OutlineIcon name="cap" size={20} strokeWidth={1.8} /></span>
                        <span class="di-brand-name">Decision<em>Intel</em></span>
                    </div>

                    <div>
                        <p class="di-eyebrow">Admissions intelligence</p>
                        <h2 class="pitch">Smarter admissions.<br /><em>Better decisions.</em></h2>
                        <p class="pitch-copy">
                            One sign-in for students, admission managers and administrators. We take you
                            straight to the right workspace.
                        </p>
                    </div>

                    <ul class="points">
                        <li>
                            <span class="point-icon"><OutlineIcon name="sparkle" size={16} /></span>
                            Predict admission outcomes
                        </li>
                        <li>
                            <span class="point-icon"><OutlineIcon name="users" size={16} /></span>
                            Understand every student lead
                        </li>
                        <li>
                            <span class="point-icon"><OutlineIcon name="chart" size={16} /></span>
                            Optimise your marketing budget
                        </li>
                    </ul>
                </div>

                <div class="form-pane">
                    <div class="form-scroll">
                        <div class="mobile-brand">
                            <span class="di-brand-mark"><OutlineIcon name="cap" size={20} strokeWidth={1.8} /></span>
                            <span class="di-brand-name">Decision<em>Intel</em></span>
                        </div>

                        <div class="intro">
                            <p class="di-eyebrow">Sign in</p>
                            <h1 class="di-title">Welcome back</h1>
                            <p class="di-muted">Use the email and password for your DecisionIntel workspace.</p>
                        </div>

                        {#if loginError}
                            <p class="di-alert di-alert-error" role="alert">{loginError}</p>
                        {/if}

                        <form onsubmit={submitLogin} novalidate>
                            <div class="control">
                                <label class="di-label" for="email">Email address</label>
                                <div class="input-wrap">
                                    <span class="input-icon"><OutlineIcon name="mail" size={18} /></span>
                                    <input
                                        class="di-input with-icon"
                                        id="email"
                                        type="email"
                                        name="email"
                                        bind:value={email}
                                        autocomplete="username"
                                        placeholder="you@example.com"
                                        required
                                    />
                                </div>
                            </div>

                            <div class="control">
                                <label class="di-label" for="password">Password</label>
                                <div class="input-wrap">
                                    <span class="input-icon"><OutlineIcon name="lock" size={18} /></span>
                                    <input
                                        class="di-input with-icon"
                                        id="password"
                                        type={loginRevealed ? 'text' : 'password'}
                                        name="password"
                                        bind:value={password}
                                        autocomplete="current-password"
                                        placeholder="Your password"
                                        required
                                    />
                                    <button
                                        type="button"
                                        class="reveal"
                                        aria-label={loginRevealed ? 'Hide password' : 'Show password'}
                                        aria-pressed={loginRevealed}
                                        onclick={() => (loginRevealed = !loginRevealed)}
                                    >
                                        <OutlineIcon name={loginRevealed ? 'eye-off' : 'eye'} size={18} />
                                    </button>
                                </div>
                            </div>

                            <button class="di-btn di-btn-primary submit" type="submit" disabled={loginBusy}>
                                {#if loginBusy}Signing in…{:else}Sign in <OutlineIcon name="arrow-right" size={18} />{/if}
                            </button>

                            <p class="switch">
                                New to DecisionIntel?
                                <button type="button" class="switch-btn" onclick={showRegister}>
                                    Create a student account
                                    <OutlineIcon name="arrow-right" size={15} />
                                </button>
                            </p>
                        </form>

                        <p class="foot-note">
                            <OutlineIcon name="shield" size={15} />
                            Managers and administrators are created by an administrator.
                        </p>
                    </div>
                </div>
            </section>

            <!-- ====================== BACK FACE : REGISTER ====================== -->
            <section class="face back" inert={!flipped} aria-hidden={!flipped} aria-label="Student registration">
                <div class="form-pane">
                    <div class="form-scroll">
                        <div class="mobile-brand">
                            <span class="di-brand-mark"><OutlineIcon name="cap" size={20} strokeWidth={1.8} /></span>
                            <span class="di-brand-name">Decision<em>Intel</em></span>
                        </div>

                        {#if regDone}
                            <div class="done">
                                <span class="done-mark"><OutlineIcon name="check" size={26} /></span>
                                <p class="di-eyebrow">Account created</p>
                                <h1 class="di-title">You are all set</h1>
                                <p class="di-muted">
                                    We created your student account for <strong>{regDone}</strong>. Sign in to
                                    start your admission journey.
                                </p>
                                <button class="di-btn di-btn-primary submit" type="button" onclick={showLogin}>
                                    Go to sign in <OutlineIcon name="arrow-right" size={18} />
                                </button>
                            </div>
                        {:else}
                            <div class="intro">
                                <p class="di-eyebrow">Student registration</p>
                                <h1 class="di-title">Create your account</h1>
                                <p class="di-muted">
                                    Tell us a little about yourself. This form scrolls inside the card.
                                </p>
                            </div>

                            {#if regError}
                                <p class="di-alert di-alert-error" role="alert">{regError}</p>
                            {/if}

                            <form onsubmit={submitRegister} novalidate>
                                <fieldset>
                                    <legend class="group">
                                        <span class="group-icon"><OutlineIcon name="user" size={15} /></span>
                                        About you
                                    </legend>
                                    <div class="grid">
                                        <div class="control span-2">
                                            <label class="di-label" for="reg-name">Full name</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.name}
                                                id="reg-name"
                                                type="text"
                                                autocomplete="name"
                                                placeholder="Your full name"
                                                value={form.name}
                                                oninput={(e) => setValue('name', e.currentTarget.value)}
                                                aria-invalid={regErrors.name ? 'true' : undefined}
                                                aria-describedby={regErrors.name ? 'err-name' : undefined}
                                                required
                                            />
                                            {#if regErrors.name}<span class="di-field-error" id="err-name">{regErrors.name}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-date_of_birth">Date of birth</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.date_of_birth}
                                                id="reg-date_of_birth"
                                                type="date"
                                                max={new Date().toISOString().slice(0, 10)}
                                                value={form.date_of_birth}
                                                oninput={(e) => setValue('date_of_birth', e.currentTarget.value)}
                                                aria-invalid={regErrors.date_of_birth ? 'true' : undefined}
                                                aria-describedby={regErrors.date_of_birth ? 'err-date_of_birth' : undefined}
                                                required
                                            />
                                            {#if regErrors.date_of_birth}<span class="di-field-error" id="err-date_of_birth">{regErrors.date_of_birth}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-gender">Gender</label>
                                            <select
                                                class="di-input"
                                                class:invalid={regErrors.gender}
                                                id="reg-gender"
                                                value={form.gender}
                                                onchange={(e) => setValue('gender', e.currentTarget.value)}
                                                aria-invalid={regErrors.gender ? 'true' : undefined}
                                                aria-describedby={regErrors.gender ? 'err-gender' : undefined}
                                                required
                                            >
                                                <option value="">Select</option>
                                                {#each GENDERS as g}<option value={g.value}>{g.label}</option>{/each}
                                            </select>
                                            {#if regErrors.gender}<span class="di-field-error" id="err-gender">{regErrors.gender}</span>{/if}
                                        </div>
                                    </div>
                                </fieldset>

                                <fieldset>
                                    <legend class="group">
                                        <span class="group-icon"><OutlineIcon name="phone" size={15} /></span>
                                        How we reach you
                                    </legend>
                                    <div class="grid">
                                        <div class="control">
                                            <label class="di-label" for="reg-email">Email address</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.email}
                                                id="reg-email"
                                                type="email"
                                                autocomplete="email"
                                                placeholder="you@example.com"
                                                value={form.email}
                                                oninput={(e) => setValue('email', e.currentTarget.value)}
                                                aria-invalid={regErrors.email ? 'true' : undefined}
                                                aria-describedby={regErrors.email ? 'err-email' : undefined}
                                                required
                                            />
                                            {#if regErrors.email}<span class="di-field-error" id="err-email">{regErrors.email}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-mobile">Mobile number</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.mobile}
                                                id="reg-mobile"
                                                type="tel"
                                                inputmode="numeric"
                                                autocomplete="tel"
                                                maxlength="10"
                                                placeholder="10 digit number"
                                                value={form.mobile}
                                                oninput={(e) => setValue('mobile', e.currentTarget.value)}
                                                aria-invalid={regErrors.mobile ? 'true' : undefined}
                                                aria-describedby={regErrors.mobile ? 'err-mobile' : undefined}
                                                required
                                            />
                                            {#if regErrors.mobile}<span class="di-field-error" id="err-mobile">{regErrors.mobile}</span>{/if}
                                        </div>
                                    </div>
                                </fieldset>

                                <fieldset>
                                    <legend class="group">
                                        <span class="group-icon"><OutlineIcon name="home" size={15} /></span>
                                        Where you live
                                    </legend>
                                    <div class="grid">
                                        <div class="control">
                                            <label class="di-label" for="reg-door_no">Door / house no.</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.door_no}
                                                id="reg-door_no"
                                                type="text"
                                                value={form.door_no}
                                                oninput={(e) => setValue('door_no', e.currentTarget.value)}
                                                aria-invalid={regErrors.door_no ? 'true' : undefined}
                                                aria-describedby={regErrors.door_no ? 'err-door_no' : undefined}
                                                required
                                            />
                                            {#if regErrors.door_no}<span class="di-field-error" id="err-door_no">{regErrors.door_no}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-pincode">PIN code</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.pincode}
                                                id="reg-pincode"
                                                type="text"
                                                inputmode="numeric"
                                                maxlength="6"
                                                placeholder="6 digits"
                                                value={form.pincode}
                                                oninput={(e) => setValue('pincode', e.currentTarget.value)}
                                                aria-invalid={regErrors.pincode ? 'true' : undefined}
                                                aria-describedby={regErrors.pincode ? 'err-pincode' : undefined}
                                                required
                                            />
                                            {#if regErrors.pincode}<span class="di-field-error" id="err-pincode">{regErrors.pincode}</span>{/if}
                                        </div>

                                        <div class="control span-2">
                                            <label class="di-label" for="reg-street">Street</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.street}
                                                id="reg-street"
                                                type="text"
                                                autocomplete="address-line1"
                                                value={form.street}
                                                oninput={(e) => setValue('street', e.currentTarget.value)}
                                                aria-invalid={regErrors.street ? 'true' : undefined}
                                                aria-describedby={regErrors.street ? 'err-street' : undefined}
                                                required
                                            />
                                            {#if regErrors.street}<span class="di-field-error" id="err-street">{regErrors.street}</span>{/if}
                                        </div>

                                        <div class="control span-2">
                                            <label class="di-label" for="reg-area">Area / locality</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.area}
                                                id="reg-area"
                                                type="text"
                                                autocomplete="address-line2"
                                                value={form.area}
                                                oninput={(e) => setValue('area', e.currentTarget.value)}
                                                aria-invalid={regErrors.area ? 'true' : undefined}
                                                aria-describedby={regErrors.area ? 'err-area' : undefined}
                                                required
                                            />
                                            {#if regErrors.area}<span class="di-field-error" id="err-area">{regErrors.area}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-city">City</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.city}
                                                id="reg-city"
                                                type="text"
                                                autocomplete="address-level2"
                                                value={form.city}
                                                oninput={(e) => setValue('city', e.currentTarget.value)}
                                                aria-invalid={regErrors.city ? 'true' : undefined}
                                                aria-describedby={regErrors.city ? 'err-city' : undefined}
                                                required
                                            />
                                            {#if regErrors.city}<span class="di-field-error" id="err-city">{regErrors.city}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-district">District</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.district}
                                                id="reg-district"
                                                type="text"
                                                value={form.district}
                                                oninput={(e) => setValue('district', e.currentTarget.value)}
                                                aria-invalid={regErrors.district ? 'true' : undefined}
                                                aria-describedby={regErrors.district ? 'err-district' : undefined}
                                                required
                                            />
                                            {#if regErrors.district}<span class="di-field-error" id="err-district">{regErrors.district}</span>{/if}
                                        </div>

                                        <div class="control span-2">
                                            <label class="di-label" for="reg-state">State</label>
                                            <select
                                                class="di-input"
                                                class:invalid={regErrors.state}
                                                id="reg-state"
                                                value={form.state}
                                                onchange={(e) => setValue('state', e.currentTarget.value)}
                                                aria-invalid={regErrors.state ? 'true' : undefined}
                                                aria-describedby={regErrors.state ? 'err-state' : undefined}
                                                required
                                            >
                                                <option value="">Select your state</option>
                                                {#each STATES as s}<option value={s}>{s}</option>{/each}
                                            </select>
                                            {#if regErrors.state}<span class="di-field-error" id="err-state">{regErrors.state}</span>{/if}
                                        </div>
                                    </div>
                                </fieldset>

                                <fieldset>
                                    <legend class="group">
                                        <span class="group-icon"><OutlineIcon name="graduation" size={15} /></span>
                                        Your education
                                    </legend>
                                    <div class="grid">
                                        <div class="control">
                                            <label class="di-label" for="reg-qualification">Highest qualification</label>
                                            <select
                                                class="di-input"
                                                class:invalid={regErrors.qualification}
                                                id="reg-qualification"
                                                value={form.qualification}
                                                onchange={(e) => setValue('qualification', e.currentTarget.value)}
                                                aria-invalid={regErrors.qualification ? 'true' : undefined}
                                                aria-describedby={regErrors.qualification ? 'err-qualification' : undefined}
                                                required
                                            >
                                                <option value="">Select</option>
                                                {#each QUALIFICATIONS as q}<option value={q}>{q}</option>{/each}
                                            </select>
                                            {#if regErrors.qualification}<span class="di-field-error" id="err-qualification">{regErrors.qualification}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-completion_year">Year of completion</label>
                                            <select
                                                class="di-input"
                                                class:invalid={regErrors.completion_year}
                                                id="reg-completion_year"
                                                value={form.completion_year}
                                                onchange={(e) => setValue('completion_year', e.currentTarget.value)}
                                                aria-invalid={regErrors.completion_year ? 'true' : undefined}
                                                aria-describedby={regErrors.completion_year ? 'err-completion_year' : undefined}
                                                required
                                            >
                                                <option value="">Select</option>
                                                {#each YEARS as y}<option value={y}>{y}</option>{/each}
                                            </select>
                                            {#if regErrors.completion_year}<span class="di-field-error" id="err-completion_year">{regErrors.completion_year}</span>{/if}
                                        </div>

                                        <div class="control span-2">
                                            <label class="di-label" for="reg-institution">Institution</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.institution}
                                                id="reg-institution"
                                                type="text"
                                                autocomplete="organization"
                                                value={form.institution}
                                                oninput={(e) => setValue('institution', e.currentTarget.value)}
                                                aria-invalid={regErrors.institution ? 'true' : undefined}
                                                aria-describedby={regErrors.institution ? 'err-institution' : undefined}
                                                required
                                            />
                                            {#if regErrors.institution}<span class="di-field-error" id="err-institution">{regErrors.institution}</span>{/if}
                                        </div>

                                        <div class="control span-2">
                                            <label class="di-label" for="reg-course_interested">Course you are interested in</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.course_interested}
                                                id="reg-course_interested"
                                                type="text"
                                                placeholder="e.g. B.Tech Computer Science"
                                                value={form.course_interested}
                                                oninput={(e) => setValue('course_interested', e.currentTarget.value)}
                                                aria-invalid={regErrors.course_interested ? 'true' : undefined}
                                                aria-describedby={regErrors.course_interested ? 'err-course_interested' : undefined}
                                                required
                                            />
                                            {#if regErrors.course_interested}<span class="di-field-error" id="err-course_interested">{regErrors.course_interested}</span>{/if}
                                        </div>
                                    </div>
                                </fieldset>

                                <fieldset>
                                    <legend class="group">
                                        <span class="group-icon"><OutlineIcon name="lock" size={15} /></span>
                                        Secure your sign-in
                                    </legend>
                                    <div class="grid">
                                        <div class="control">
                                            <label class="di-label" for="reg-password">Password</label>
                                            <div class="input-wrap">
                                                <input
                                                    class="di-input with-reveal"
                                                    class:invalid={regErrors.password}
                                                    id="reg-password"
                                                    type={regRevealed ? 'text' : 'password'}
                                                    autocomplete="new-password"
                                                    placeholder="At least 12 characters"
                                                    value={form.password}
                                                    oninput={(e) => setValue('password', e.currentTarget.value)}
                                                    aria-invalid={regErrors.password ? 'true' : undefined}
                                                    aria-describedby={regErrors.password ? 'err-password' : undefined}
                                                    required
                                                />
                                                <button
                                                    type="button"
                                                    class="reveal"
                                                    aria-label={regRevealed ? 'Hide password' : 'Show password'}
                                                    aria-pressed={regRevealed}
                                                    onclick={() => (regRevealed = !regRevealed)}
                                                >
                                                    <OutlineIcon name={regRevealed ? 'eye-off' : 'eye'} size={17} />
                                                </button>
                                            </div>
                                            {#if regErrors.password}<span class="di-field-error" id="err-password">{regErrors.password}</span>{/if}
                                        </div>

                                        <div class="control">
                                            <label class="di-label" for="reg-confirm_password">Confirm password</label>
                                            <input
                                                class="di-input"
                                                class:invalid={regErrors.confirm_password}
                                                id="reg-confirm_password"
                                                type={regRevealed ? 'text' : 'password'}
                                                autocomplete="new-password"
                                                placeholder="Repeat your password"
                                                value={form.confirm_password}
                                                oninput={(e) => setValue('confirm_password', e.currentTarget.value)}
                                                aria-invalid={regErrors.confirm_password ? 'true' : undefined}
                                                aria-describedby={regErrors.confirm_password ? 'err-confirm_password' : undefined}
                                                required
                                            />
                                            {#if regErrors.confirm_password}<span class="di-field-error" id="err-confirm_password">{regErrors.confirm_password}</span>{/if}
                                        </div>
                                    </div>
                                </fieldset>

                                <button class="di-btn di-btn-primary submit" type="submit" disabled={regBusy}>
                                    {#if regBusy}Creating account…{:else}Create student account <OutlineIcon name="arrow-right" size={18} />{/if}
                                </button>

                                <p class="switch">
                                    Already have an account?
                                    <button type="button" class="switch-btn" onclick={showLogin}>
                                        <span class="flip-back"><OutlineIcon name="arrow-right" size={15} /></span>
                                        Sign in instead
                                    </button>
                                </p>
                            </form>
                        {/if}
                    </div>
                </div>

                <div class="brand-pane right">
                    <div class="brand">
                        <span class="di-brand-mark"><OutlineIcon name="cap" size={20} strokeWidth={1.8} /></span>
                        <span class="di-brand-name">Decision<em>Intel</em></span>
                    </div>

                    <div>
                        <span class="art"><OutlineIcon name="graduation" size={30} strokeWidth={1.4} /></span>
                        <h2 class="pitch">Start your<br /><em>admission journey.</em></h2>
                        <p class="pitch-copy">
                            Public registration is for students. Your details let us personalise course
                            guidance, predict outcomes and keep your enquiry on track.
                        </p>
                    </div>

                    <ul class="points">
                        <li><span class="point-icon"><OutlineIcon name="check" size={16} /></span>Submit and track enquiries</li>
                        <li><span class="point-icon"><OutlineIcon name="check" size={16} /></span>Personalised course guidance</li>
                        <li><span class="point-icon"><OutlineIcon name="check" size={16} /></span>Admission outcome insights</li>
                    </ul>
                </div>
            </section>
        </div>
    </div>
</div>

<style>
    /* Page background follows the global theme (see di-light.css), so the card
       is never ringed by the wrong palette. */

    .auth {
        --flip-h: clamp(540px, calc(100dvh - 8.5rem), 720px);
        position: relative;
        min-height: 100dvh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        padding: clamp(1rem, 3vw, 2rem) clamp(0.75rem, 3vw, 2rem);
        background-color: var(--di-bg);
        overflow: hidden;
    }

    .glow {
        position: absolute;
        border-radius: 999px;
        filter: blur(110px);
        pointer-events: none;
        z-index: 0;
    }
    .glow-a { top: -8rem; right: -6rem; width: 30rem; height: 30rem; background: rgba(106, 49, 196, 0.14); }
    .glow-b { bottom: -10rem; left: -8rem; width: 32rem; height: 32rem; background: rgba(106, 49, 196, 0.18); }

    .back {
        position: relative;
        z-index: 2;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--di-muted);
        text-decoration: none;
        transition: color 150ms ease;
    }
    .back :global(svg) { transform: rotate(180deg); }

    /* Theme toggle parked in the same top-right corner as the back link, so
       the flip-card layout below is untouched. */
    .auth-theme {
        position: absolute;
        top: 1.25rem;
        right: 1.5rem;
        z-index: 3;
    }
    @media (max-width: 40rem) {
        .auth-theme { top: 1rem; right: 1rem; }
    }
    .back:hover { color: var(--di-accent); }
    .back:focus-visible { outline: 2px solid var(--di-accent); outline-offset: 3px; border-radius: 6px; }

    /* ---------------- 3D flip ---------------- */
    .stage {
        position: relative;
        z-index: 1;
        width: 100%;
        max-width: 68rem;
        perspective: 1800px;
    }

    .flip {
        position: relative;
        height: var(--flip-h);
        transform-style: preserve-3d;
        transition: transform 0.85s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .flip.flipped { transform: rotateY(-180deg); }

    .face {
        position: absolute;
        inset: 0;
        display: flex;
        overflow: hidden;
        border-radius: 26px;
        background-color: var(--di-surface);
        border: 1px solid var(--di-border);
        box-shadow: 0 32px 70px -42px rgba(38, 34, 48, 0.45);
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }
    .face.back { transform: rotateY(180deg); }

    /* ---------------- brand pane ---------------- */
    .brand-pane {
        display: none;
        flex: 0 0 40%;
        flex-direction: column;
        justify-content: space-between;
        gap: 1.5rem;
        padding: clamp(1.5rem, 2.6vw, 2.5rem);
        background-image: linear-gradient(165deg, #F6F0FE 0%, #FFFFFF 58%, #F3EBFC 100%);
        border-right: 1px solid var(--di-border);
    }
    /* The registration panel sits on the right of the flipped face. It keeps
       the same 40% width as the login panel, and is pinned to the full height
       of the card so the light surface runs edge to edge from the top border
       radius to the bottom one. `height: 100%` resolves against the face,
       whose height is fixed by `position: absolute; inset: 0`. */
    .brand-pane.right {
        border-right: 0;
        border-left: 1px solid var(--di-border);
        align-self: stretch;
        height: 100%;
    }
    @media (min-width: 62rem) { .brand-pane { display: flex; } }

    /* The brand pane keeps its light gradient in *both* themes, so it must
       never inherit the dark-theme ink tokens: --di-text is #FFFFFF and
       --di-muted is #C9C5CE there, which is white-on-cream. The rules below
       repoint only the text/foreground colours onto the light-pane palette,
       leaving the background, size, spacing and layout untouched. Light mode
       needs no change, so the whole block is gated on `:not(.di-light)`. */
    :global(html:not(.di-light)) .brand-pane :global(.di-brand-name) { color: #1E1A26; }
    :global(html:not(.di-light)) .brand-pane :global(.di-brand-name) :global(em) { color: #6A31C4; }
    :global(html:not(.di-light)) .brand-pane :global(.di-eyebrow) { color: #6A31C4; }
    :global(html:not(.di-light)) .brand-pane .pitch { color: #1E1A26; }
    :global(html:not(.di-light)) .brand-pane .pitch :global(em) { color: #6A31C4; }
    :global(html:not(.di-light)) .brand-pane .pitch-copy { color: #4A4454; }
    :global(html:not(.di-light)) .brand-pane .points li { color: #2A2434; }
    :global(html:not(.di-light)) .brand-pane .point-icon {
        color: #5B21B6;
        background-color: rgba(106, 49, 196, .10);
        border-color: rgba(106, 49, 196, .22);
    }
    /* The logo tile keeps its purple sheen, but the dark theme's sheen is a
       light purple, so a white glyph would vanish. Dark purple reads on it. */
    :global(html:not(.di-light)) .brand-pane .art { color: #3B0F73; }

    .brand { display: flex; align-items: center; gap: 0.65rem; }
    .brand :global(em) { font-style: normal; color: var(--di-accent); }

    .pitch {
        margin: 0.5rem 0 0.75rem;
        font-size: clamp(1.5rem, 2.1vw, 1.95rem);
        font-weight: 700;
        line-height: 1.2;
        letter-spacing: -0.02em;
        color: var(--di-text);
    }
    .pitch :global(em) { font-style: normal; color: var(--di-accent); }
    .pitch-copy { margin: 0; font-size: 0.875rem; line-height: 1.65; color: var(--di-muted); }

    .points { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.5rem; }
    .points li {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--di-text);
    }
    .point-icon {
        display: grid;
        place-items: center;
        width: 1.9rem;
        height: 1.9rem;
        flex: none;
        border-radius: 10px;
        color: var(--di-accent);
        background-color: var(--di-accent-soft);
        border: 1px solid var(--di-accent-line);
    }

    .art {
        display: grid;
        place-items: center;
        width: 3.75rem;
        height: 3.75rem;
        margin-bottom: 1.1rem;
        border-radius: 18px;
        color: #ffffff;
        background-image: var(--di-accent-sheen);
        box-shadow: 0 14px 26px -14px rgba(106, 49, 196, 0.95);
    }

    /* ---------------- form pane ---------------- */
    /* height:100% + min-height:0 + overflow:hidden keep the long registration
       form inside the card: the pane is the card, the form scrolls inside it. */
    .form-pane {
        flex: 1 1 auto;
        min-width: 0;
        min-height: 0;
        height: 100%;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        background-color: var(--di-surface);
    }

    /* The long registration form scrolls inside the card, never the page. */
    .form-scroll {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;
        padding: clamp(1.25rem, 2.4vw, 2.25rem);
        display: flex;
        flex-direction: column;
        gap: 1.1rem;
    }
    .form-scroll::-webkit-scrollbar { width: 10px; }
    .form-scroll::-webkit-scrollbar-track { background: transparent; }
    .form-scroll::-webkit-scrollbar-thumb { background-color: #6F6979; border-radius: 999px; border: 3px solid var(--di-surface); }

    .mobile-brand { display: flex; align-items: center; gap: 0.6rem; }
    @media (min-width: 62rem) { .mobile-brand { display: none; } }
    .mobile-brand :global(em) { font-style: normal; color: var(--di-accent); }

    .intro { display: grid; gap: 0.4rem; }
    .intro :global(.di-title) { font-size: clamp(1.6rem, 2.4vw, 1.9rem); }

    form { display: flex; flex-direction: column; gap: 1rem; }

    .control { min-width: 0; }
    .grid { display: grid; grid-template-columns: 1fr; gap: 0.85rem; }
    @media (min-width: 30rem) {
        .grid { grid-template-columns: 1fr 1fr; }
        .span-2 { grid-column: 1 / -1; }
    }

    fieldset { border: 0; margin: 0; padding: 0; }
    .group {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0;
        margin: 0 0 0.7rem;
        font-size: 0.6875rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--di-accent);
    }
    .group-icon {
        display: grid;
        place-items: center;
        width: 1.6rem;
        height: 1.6rem;
        border-radius: 8px;
        color: var(--di-accent);
        background-color: var(--di-accent-soft);
    }

    :global(.di-input:focus-visible) { outline: none; border-color: var(--di-accent); box-shadow: 0 0 0 3px rgba(106, 49, 196, 0.18); }
    :global(.di-input.invalid) { border-color: #FBEAEE; }
    select.di-input { appearance: none; }

    .input-wrap { position: relative; display: flex; align-items: center; }
    .input-icon {
        position: absolute;
        left: 0.75rem;
        display: grid;
        place-items: center;
        color: var(--di-muted);
        pointer-events: none;
    }
    .with-icon { padding-left: 2.6rem; }
    .with-reveal { padding-right: 2.75rem; }
    .reveal {
        position: absolute;
        right: 0.4rem;
        display: grid;
        place-items: center;
        width: 2rem;
        height: 2rem;
        border: 0;
        border-radius: 8px;
        background-color: transparent;
        color: var(--di-muted);
        cursor: pointer;
        transition: color 150ms ease, background-color 150ms ease;
    }
    .reveal:hover { color: var(--di-accent); background-color: var(--di-accent-soft); }
    .reveal:focus-visible { outline: 2px solid var(--di-accent); outline-offset: 1px; }

    .submit { width: 100%; margin-top: 0.25rem; }
    .submit :global(svg) { transition: transform 200ms ease; }
    .submit:hover :global(svg) { transform: translateX(3px); }

    .switch {
        margin: 0.1rem 0 0;
        text-align: center;
        font-size: 0.8125rem;
        color: var(--di-muted);
    }
    .switch-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        margin-left: 0.3rem;
        border: 0;
        background: none;
        padding: 0;
        font: inherit;
        font-weight: 700;
        color: var(--di-accent);
        cursor: pointer;
        text-decoration: underline;
        text-underline-offset: 3px;
    }
    .switch-btn:hover { color: var(--di-accent-ink); }
    .switch-btn:focus-visible { outline: 2px solid var(--di-accent); outline-offset: 3px; border-radius: 6px; }
    .flip-back { display: inline-flex; }
    .flip-back :global(svg) { transform: rotate(180deg); }

    .foot-note {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        margin: auto 0 0;
        font-size: 0.75rem;
        color: var(--di-muted);
    }

    .done { display: grid; gap: 0.5rem; justify-items: start; margin: auto 0; }
    .done-mark {
        display: grid;
        place-items: center;
        width: 3.5rem;
        height: 3.5rem;
        border-radius: 20px;
        color: var(--di-green-ink);
        background-color: var(--di-green-soft);
        border: 1px solid #E7F2EC;
        margin-bottom: 0.5rem;
    }
    .done .submit { margin-top: 1rem; }

    @media (prefers-reduced-motion: reduce) {
        .flip { transition: none; }
    }
</style>
