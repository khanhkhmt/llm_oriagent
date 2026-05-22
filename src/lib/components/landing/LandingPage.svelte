<script lang="ts">
	import { goto } from '$app/navigation';
	import { config, WEBUI_NAME } from '$lib/stores';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	const features = [
		{
			icon: '💬',
			title: 'Chat với nhiều model AI',
			desc: 'Hỗ trợ OpenAI, Anthropic, Google Gemini và nhiều provider khác trong một giao diện duy nhất.'
		},
		{
			icon: '🦙',
			title: 'Ollama & Local Models',
			desc: 'Chạy model AI ngay trên máy chủ của bạn, hoàn toàn offline, bảo mật dữ liệu tuyệt đối.'
		},
		{
			icon: '📚',
			title: 'Knowledge / RAG',
			desc: 'Upload tài liệu, tạo knowledge base và để AI trả lời dựa trên dữ liệu của bạn.'
		},
		{
			icon: '🔒',
			title: 'Self-hosted & Bảo mật',
			desc: 'Toàn quyền kiểm soát dữ liệu, không phụ thuộc cloud, phù hợp doanh nghiệp.'
		},
		{
			icon: '🛠️',
			title: 'Tools & Extensions',
			desc: 'Mở rộng khả năng AI với custom tools, Python functions và MCP protocol.'
		},
		{
			icon: '👥',
			title: 'Quản lý người dùng',
			desc: 'RBAC, phân quyền chi tiết, hỗ trợ LDAP, OAuth và SCIM provisioning.'
		}
	];

	$: googleOAuthEnabled = !!$config?.oauth?.providers?.google;
</script>

<div class="min-h-screen bg-white dark:bg-gray-900 flex flex-col">
	<!-- Header -->
	<header
		class="fixed top-0 left-0 right-0 z-50 border-b border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md"
	>
		<div class="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
			<!-- Logo -->
			<a href="/" class="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
				<img src="/favicon.png" alt="logo" class="size-7 rounded-lg" on:error={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
				<span class="font-semibold text-gray-900 dark:text-white text-base">
					{$WEBUI_NAME || 'Open WebUI'}
				</span>
			</a>

			<!-- Nav buttons -->
			<div class="flex items-center gap-2">
				<a
					href="/auth"
					class="px-4 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
				>
					Đăng nhập
				</a>
				<a
					href="/signup"
					class="px-4 py-1.5 text-sm font-medium bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-200 transition-colors"
				>
					Đăng ký
				</a>
			</div>
		</div>
	</header>

	<!-- Hero Section -->
	<main class="flex-1 flex flex-col">
		<section class="pt-32 pb-20 px-4 sm:px-6 text-center">
			<div class="max-w-3xl mx-auto">
				<div
					class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800 mb-6"
				>
					<span class="size-1.5 rounded-full bg-blue-500 animate-pulse"></span>
					Self-hosted AI Platform
				</div>

				<h1 class="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white leading-tight mb-5">
					AI mạnh mẽ,<br />
					<span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-violet-500">
						hoàn toàn do bạn kiểm soát
					</span>
				</h1>

				<p class="text-base sm:text-lg text-gray-500 dark:text-gray-400 mb-10 max-w-xl mx-auto leading-relaxed">
					Nền tảng AI chat tự hosted, hỗ trợ Ollama, OpenAI, Anthropic và nhiều model khác.
					Dữ liệu của bạn, máy chủ của bạn.
				</p>

				<!-- CTA Buttons -->
				<div class="flex flex-col sm:flex-row gap-3 justify-center items-center">
					<a
						href="/auth"
						class="w-full sm:w-auto px-6 py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium rounded-xl hover:bg-gray-700 dark:hover:bg-gray-200 transition-colors text-sm"
					>
						Đăng nhập
					</a>

					<a
						href="/signup"
						class="w-full sm:w-auto px-6 py-3 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm"
					>
						Tạo tài khoản miễn phí
					</a>

					{#if googleOAuthEnabled}
						<button
							class="w-full sm:w-auto flex items-center justify-center gap-2.5 px-6 py-3 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm"
							on:click={() => {
								window.location.href = `${WEBUI_BASE_URL}/oauth/google/login`;
							}}
						>
							<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" class="size-4.5" aria-hidden="true">
								<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
								<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
								<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
								<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
								<path fill="none" d="M0 0h48v48H0z" />
							</svg>
							Tiếp tục với Google
						</button>
					{/if}
				</div>

				{#if !googleOAuthEnabled}
					<p class="mt-4 text-xs text-gray-400 dark:text-gray-600">
						Google OAuth chưa được cấu hình.
						<a href="/signup" class="underline hover:text-gray-600">Đăng ký bằng email</a>
					</p>
				{/if}
			</div>
		</section>

		<!-- Features Grid -->
		<section class="py-16 px-4 sm:px-6 bg-gray-50 dark:bg-gray-800/30">
			<div class="max-w-5xl mx-auto">
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white text-center mb-2">
					Tất cả tính năng bạn cần
				</h2>
				<p class="text-gray-500 dark:text-gray-400 text-center text-sm mb-10">
					Một nền tảng, nhiều khả năng
				</p>

				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each features as f}
						<div
							class="p-5 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 hover:border-gray-200 dark:hover:border-gray-600 transition-colors"
						>
							<div class="text-2xl mb-3">{f.icon}</div>
							<h3 class="font-semibold text-gray-900 dark:text-white text-sm mb-1.5">{f.title}</h3>
							<p class="text-gray-500 dark:text-gray-400 text-xs leading-relaxed">{f.desc}</p>
						</div>
					{/each}
				</div>
			</div>
		</section>

		<!-- Bottom CTA -->
		<section class="py-16 px-4 sm:px-6 text-center">
			<div class="max-w-xl mx-auto">
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
					Sẵn sàng bắt đầu?
				</h2>
				<p class="text-gray-500 dark:text-gray-400 text-sm mb-8">
					Đăng nhập ngay hoặc tạo tài khoản để trải nghiệm AI mạnh mẽ.
				</p>
				<div class="flex flex-col sm:flex-row gap-3 justify-center">
					<a
						href="/auth"
						class="px-6 py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium rounded-xl hover:bg-gray-700 dark:hover:bg-gray-200 transition-colors text-sm"
					>
						Đăng nhập
					</a>
					<a
						href="/signup"
						class="px-6 py-3 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-sm"
					>
						Tạo tài khoản
					</a>
				</div>
			</div>
		</section>
	</main>

	<!-- Footer -->
	<footer class="border-t border-gray-100 dark:border-gray-800 py-6 px-4 sm:px-6">
		<div class="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-400 dark:text-gray-600">
			<span>© {new Date().getFullYear()} {$WEBUI_NAME || 'Open WebUI'}. Self-hosted AI Platform.</span>
			<div class="flex items-center gap-4">
				<a href="/signup" class="hover:text-gray-600 dark:hover:text-gray-400 transition-colors">Đăng ký</a>
				<a href="/auth" class="hover:text-gray-600 dark:hover:text-gray-400 transition-colors">Đăng nhập</a>
			</div>
		</div>
	</footer>
</div>
