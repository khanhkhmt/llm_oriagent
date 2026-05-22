<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { config, WEBUI_NAME } from '$lib/stores';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { userSignUp } from '$lib/apis/auths';
	import { toast } from 'svelte-sonner';

	let name = '';
	let email = '';
	let password = '';
	let confirmPassword = '';
	let loading = false;
	let signupEnabled = false;
	let googleOAuthEnabled = false;

	$: signupEnabled = $config?.features?.enable_signup ?? false;
	$: googleOAuthEnabled = !!$config?.oauth?.providers?.google;

	const handleSubmit = async () => {
		if (!name.trim()) {
			toast.error('Vui lòng nhập họ tên.');
			return;
		}
		if (!email.trim()) {
			toast.error('Vui lòng nhập email.');
			return;
		}
		if (password.length < 8) {
			toast.error('Mật khẩu phải có ít nhất 8 ký tự.');
			return;
		}
		if (password !== confirmPassword) {
			toast.error('Mật khẩu xác nhận không khớp.');
			return;
		}

		loading = true;
		try {
			const res = await userSignUp(name.trim(), email.trim(), password, '');
			if (res?.token) {
				localStorage.setItem('token', res.token);
				toast.success('Đăng ký thành công! Đang chuyển hướng...');
				await goto('/');
			}
		} catch (err: any) {
			const msg = typeof err === 'string' ? err : err?.detail ?? 'Đăng ký thất bại. Vui lòng thử lại.';
			toast.error(msg);
		} finally {
			loading = false;
		}
	};
</script>

<svelte:head>
	<title>Đăng ký — {$WEBUI_NAME || 'Open WebUI'}</title>
</svelte:head>

<div class="min-h-screen bg-white dark:bg-gray-900 flex flex-col">
	<!-- Header -->
	<header class="fixed top-0 left-0 right-0 z-50 border-b border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md">
		<div class="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
			<a href="/" class="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
				<img
					src="/favicon.png"
					alt="logo"
					class="size-7 rounded-lg"
					on:error={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
				/>
				<span class="font-semibold text-gray-900 dark:text-white text-base">
					{$WEBUI_NAME || 'Open WebUI'}
				</span>
			</a>
			<a
				href="/auth"
				class="px-4 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
			>
				Đã có tài khoản? Đăng nhập
			</a>
		</div>
	</header>

	<!-- Main -->
	<main class="flex-1 flex items-center justify-center pt-20 pb-12 px-4">
		<div class="w-full max-w-md">
			<!-- Card -->
			<div class="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-2xl shadow-sm p-8">
				<div class="text-center mb-7">
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-1.5">Tạo tài khoản</h1>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						Đăng ký miễn phí để trải nghiệm AI mạnh mẽ
					</p>
				</div>

				{#if !signupEnabled}
					<!-- Signup disabled notice -->
					<div class="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4 mb-5 text-center">
						<p class="text-sm font-medium text-amber-700 dark:text-amber-400 mb-1">
							Đăng ký tạm thời bị tắt
						</p>
						<p class="text-xs text-amber-600 dark:text-amber-500">
							Quản trị viên chưa bật tính năng đăng ký. Vui lòng liên hệ admin.
						</p>
					</div>
				{/if}

				<!-- Google OAuth -->
				{#if googleOAuthEnabled}
					<button
						class="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors mb-4"
						on:click={() => { window.location.href = `${WEBUI_BASE_URL}/oauth/google/login`; }}
					>
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="size-4.5" aria-hidden="true">
							<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
							<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
							<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
							<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
							<path fill="none" d="M0 0h48v48H0z" />
						</svg>
						Đăng ký với Google
					</button>

					<div class="relative mb-4">
						<div class="absolute inset-0 flex items-center">
							<div class="w-full border-t border-gray-100 dark:border-gray-700"></div>
						</div>
						<div class="relative flex justify-center">
							<span class="px-3 bg-white dark:bg-gray-800 text-xs text-gray-400 dark:text-gray-500">hoặc đăng ký bằng email</span>
						</div>
					</div>
				{/if}

				<!-- Signup Form -->
				<form on:submit|preventDefault={handleSubmit} class="space-y-4" class:opacity-60={!signupEnabled} class:pointer-events-none={!signupEnabled}>
					<div>
						<label for="name" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
							Họ và tên
						</label>
						<input
							id="name"
							type="text"
							bind:value={name}
							placeholder="Nguyễn Văn A"
							autocomplete="name"
							class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition"
							required
						/>
					</div>

					<div>
						<label for="email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
							Email
						</label>
						<input
							id="email"
							type="email"
							bind:value={email}
							placeholder="ban@example.com"
							autocomplete="email"
							class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition"
							required
						/>
					</div>

					<div>
						<label for="password" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
							Mật khẩu
						</label>
						<input
							id="password"
							type="password"
							bind:value={password}
							placeholder="Ít nhất 8 ký tự"
							autocomplete="new-password"
							class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition"
							required
						/>
					</div>

					<div>
						<label for="confirmPassword" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
							Xác nhận mật khẩu
						</label>
						<input
							id="confirmPassword"
							type="password"
							bind:value={confirmPassword}
							placeholder="Nhập lại mật khẩu"
							autocomplete="new-password"
							class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition"
							required
						/>
					</div>

					<button
						type="submit"
						disabled={loading || !signupEnabled}
						class="w-full py-2.5 px-4 bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-sm font-medium rounded-xl hover:bg-gray-700 dark:hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 mt-2"
					>
						{#if loading}
							<svg class="animate-spin size-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							Đang tạo tài khoản...
						{:else}
							Tạo tài khoản
						{/if}
					</button>
				</form>

				<p class="text-center text-xs text-gray-500 dark:text-gray-400 mt-5">
					Đã có tài khoản?
					<a href="/auth" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">Đăng nhập</a>
				</p>
			</div>

			<p class="text-center text-xs text-gray-400 dark:text-gray-600 mt-4">
				<a href="/" class="hover:text-gray-600 dark:hover:text-gray-400 transition-colors">← Về trang chủ</a>
			</p>
		</div>
	</main>
</div>
