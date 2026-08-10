<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';

	import { user, config } from '$lib/stores';
	import { createAPIKey, getAPIKeys, deleteAPIKey } from '$lib/apis/auths';
	import { copyToClipboard } from '$lib/utils';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let APIKeys = [];
	let APIKeyCopied: Record<string, boolean> = {};
	let JWTTokenCopied = false;

	const createAPIKeyHandler = async () => {
		try {
			const newKey = await createAPIKey(localStorage.token);
			if (newKey) {
				toast.success($i18n.t('API Key created.'));
				APIKeys = [newKey, ...APIKeys];
			} else {
				toast.error($i18n.t('Failed to create API Key.'));
			}
		} catch (err) {
			console.error('Create API Key error:', err);
			toast.error(err?.toString() || $i18n.t('Failed to create API Key.'));
		}
	};

	const deleteAPIKeyHandler = async (key_id: string) => {
		try {
			const success = await deleteAPIKey(localStorage.token, key_id);
			if (success) {
				toast.success($i18n.t('API Key deleted.'));
				APIKeys = APIKeys.filter(k => k.id !== key_id);
			} else {
				toast.error($i18n.t('Failed to delete API Key.'));
			}
		} catch (err) {
			toast.error(err?.toString() || $i18n.t('Failed to delete API Key.'));
		}
	};

	onMount(async () => {
		APIKeys = await getAPIKeys(localStorage.token).catch((error) => {
			console.log(error);
			return [];
		});
		loaded = true;
	});
</script>

<div id="tab-api-keys" class="flex flex-col h-full justify-between text-sm">
	<div class="overflow-y-scroll max-h-[28rem] md:max-h-full">
		<div class="space-y-1">
			<div>
				<div class="text-base font-medium">{$i18n.t('API Keys')}</div>
				<div class="text-xs text-gray-500 mt-0.5">
					{$i18n.t('Manage your API keys for third-party integrations.')}
				</div>
			</div>
		</div>

		{#if loaded}
			<!-- API Key Section -->
				<div class="mt-5">
					<div class="flex justify-between items-center mb-3">
						<div class="text-sm font-medium">{$i18n.t('API Key')}</div>
					</div>

					<div class="bg-gray-50 dark:bg-gray-850/50 rounded-xl p-4">
						<div class="flex items-center justify-between mb-4">
							<div class="text-xs text-gray-500 dark:text-gray-400 flex-1">
								{$i18n.t('Use these API keys to authenticate requests to the OriAgent Public API.')}
							</div>
							<button
								class="flex gap-1.5 items-center font-medium px-3.5 py-1.5 rounded-lg bg-gray-100/70 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition text-xs flex-shrink-0"
								on:click={() => {
									createAPIKeyHandler();
								}}
							>
								<Plus strokeWidth="2" className="size-3.5" />
								{$i18n.t('Create new key')}
							</button>
						</div>

						<div class="space-y-3">
							{#each APIKeys as key (key.id)}
								<div class="flex items-center gap-2">
									<div class="flex-1">
										<SensitiveInput value={key.key} readOnly={true} />
									</div>

									<Tooltip content={$i18n.t('Copy API Key')}>
										<button
											class="px-2 py-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 transition rounded-lg"
											aria-label={$i18n.t('Copy API Key')}
											on:click={() => {
												copyToClipboard(key.key);
												APIKeyCopied[key.id] = true;
												setTimeout(() => {
													APIKeyCopied[key.id] = false;
												}, 2000);
											}}
										>
											{#if APIKeyCopied[key.id]}
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 20 20"
													fill="currentColor"
													class="w-4 h-4 text-green-500"
												>
													<path
														fill-rule="evenodd"
														d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
														clip-rule="evenodd"
													/>
												</svg>
											{:else}
												<svg
													xmlns="http://www.w3.org/2000/svg"
													viewBox="0 0 16 16"
													fill="currentColor"
													class="w-4 h-4"
												>
													<path
														fill-rule="evenodd"
														d="M11.986 3H12a2 2 0 0 1 2 2v6a2 2 0 0 1-1.5 1.937V7A2.5 2.5 0 0 0 10 4.5H4.063A2 2 0 0 1 6 3h.014A2.25 2.25 0 0 1 8.25 1h1.5a2.25 2.25 0 0 1 2.236 2ZM10.5 4v-.75a.75.75 0 0 0-.75-.75h-1.5a.75.75 0 0 0-.75.75V4h3Z"
														clip-rule="evenodd"
													/>
													<path
														fill-rule="evenodd"
														d="M3 6a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1H3Zm1.75 2.5a.75.75 0 0 0 0 1.5h3.5a.75.75 0 0 0 0-1.5h-3.5ZM4 11.75a.75.75 0 0 1 .75-.75h3.5a.75.75 0 0 1 0 1.5h-3.5a.75.75 0 0 1-.75-.75Z"
														clip-rule="evenodd"
													/>
												</svg>
											{/if}
										</button>
									</Tooltip>

									<Tooltip content={$i18n.t('Delete API Key')}>
										<button
											class="px-2 py-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 transition rounded-lg text-red-500"
											aria-label={$i18n.t('Delete API Key')}
											on:click={() => {
												deleteAPIKeyHandler(key.id);
											}}
										>
											<GarbageBin className="w-4 h-4" />
										</button>
									</Tooltip>
								</div>
							{/each}

							{#if APIKeys.length === 0}
								<div class="text-center text-xs text-gray-500 py-4">
									{$i18n.t('No API keys created yet.')}
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- JWT Token Section (admin only) -->
				{#if $user?.role === 'admin'}
					<div class="mt-5">
						<div class="flex justify-between items-center mb-3">
							<div class="text-sm font-medium">{$i18n.t('JWT Token')}</div>
							<div class="text-xs text-gray-400">{$i18n.t('Admin Only')}</div>
						</div>

						<div class="bg-gray-50 dark:bg-gray-850/50 rounded-xl p-4">
							<div class="text-xs text-gray-500 dark:text-gray-400 mb-3">
								{$i18n.t('This is your session JWT token. Use it for internal API calls.')}
							</div>

							<div class="flex items-center gap-2">
								<div class="flex-1">
									<SensitiveInput value={localStorage.token} readOnly={true} />
								</div>

								<Tooltip content={$i18n.t('Copy Token')}>
									<button
										class="px-2 py-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 transition rounded-lg"
										aria-label={$i18n.t('Copy Token')}
										on:click={() => {
											copyToClipboard(localStorage.token);
											JWTTokenCopied = true;
											setTimeout(() => {
												JWTTokenCopied = false;
											}, 2000);
										}}
									>
										{#if JWTTokenCopied}
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 20 20"
												fill="currentColor"
												class="w-4 h-4 text-green-500"
											>
												<path
													fill-rule="evenodd"
													d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
													clip-rule="evenodd"
												/>
											</svg>
										{:else}
											<svg
												xmlns="http://www.w3.org/2000/svg"
												viewBox="0 0 16 16"
												fill="currentColor"
												class="w-4 h-4"
											>
												<path
													fill-rule="evenodd"
													d="M11.986 3H12a2 2 0 0 1 2 2v6a2 2 0 0 1-1.5 1.937V7A2.5 2.5 0 0 0 10 4.5H4.063A2 2 0 0 1 6 3h.014A2.25 2.25 0 0 1 8.25 1h1.5a2.25 2.25 0 0 1 2.236 2ZM10.5 4v-.75a.75.75 0 0 0-.75-.75h-1.5a.75.75 0 0 0-.75.75V4h3Z"
													clip-rule="evenodd"
												/>
												<path
													fill-rule="evenodd"
													d="M3 6a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1H3Zm1.75 2.5a.75.75 0 0 0 0 1.5h3.5a.75.75 0 0 0 0-1.5h-3.5ZM4 11.75a.75.75 0 0 1 .75-.75h3.5a.75.75 0 0 1 0 1.5h-3.5a.75.75 0 0 1-.75-.75Z"
													clip-rule="evenodd"
												/>
											</svg>
										{/if}
									</button>
								</Tooltip>
							</div>
						</div>
					</div>
				{/if}

				<!-- Detailed API Documentation Section -->
				<div class="mt-5">
					<div class="text-sm font-medium mb-3">{$i18n.t('API Documentation')}</div>

					<div class="bg-gray-50 dark:bg-gray-850/50 rounded-xl p-4 space-y-6">
						<!-- Base Info -->
						<div>
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
								{$i18n.t('Base URL & Authentication')}
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
								{$i18n.t('All requests must include your API key in the Authorization header.')}
							</div>
							<div class="font-mono text-xs bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2 select-all mb-2">
								https://llm.oriagent.com/api/public/v1
							</div>
							<pre class="font-mono text-xs bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2 overflow-x-auto whitespace-pre-wrap text-blue-600 dark:text-blue-400">Authorization: Bearer sk-your-api-key</pre>
						</div>

						<!-- Chat Completions -->
						<div>
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2">
								<span class="font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded text-[10px]">POST</span>
								/chat/completions
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
								{$i18n.t('Generate a chat completion. Fully compatible with OpenAI SDK.')}
							</div>
							<div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
								<div class="text-[10px] font-semibold text-gray-500 px-2 py-1 uppercase tracking-wider">cURL Example</div>
								<pre class="font-mono text-xs px-2 py-1 overflow-x-auto whitespace-pre-wrap">curl -X POST "https://llm.oriagent.com/api/public/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '&#123;
    "model": "Qwen/Qwen3.5-2B",
    "messages": [&#123;"role": "user", "content": "Hello!"}]
  &#125;'</pre>
							</div>
						</div>

						<!-- Python SDK -->
						<div>
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
								{$i18n.t('Python Example (OpenAI SDK)')}
							</div>
							<div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
								<pre class="font-mono text-xs px-2 py-1 overflow-x-auto whitespace-pre-wrap text-green-700 dark:text-green-400">from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://llm.oriagent.com/api/public/v1"
)

response = client.chat.completions.create(
    model="Qwen/Qwen3.5-2B",
    messages=[&#123;"role": "user", "content": "Hello!"&#125;]
)
print(response.choices[0].message.content)</pre>
							</div>
						</div>

						<!-- Agents (ReAct) -->
						<div>
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2">
								<span class="font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded text-[10px]">POST</span>
								/agents/run
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
								{$i18n.t('Run a server-side ReAct agent. OriAgent executes internal tools and returns the final answer.')}
							</div>
							<div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
								<pre class="font-mono text-xs px-2 py-1 overflow-x-auto whitespace-pre-wrap">curl -X POST "https://llm.oriagent.com/api/public/v1/agents/run" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '&#123;
    "model": "Qwen/Qwen3.5-2B",
    "messages": [&#123;"role": "user", "content": "What time is it in UTC?"&#125;],
    "allowed_tools": ["get_time"],
    "max_steps": 4
  &#125;'</pre>
							</div>
						</div>

						<!-- File Upload -->
						<div>
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2">
								<span class="font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded text-[10px]">POST</span>
								/files
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
								{$i18n.t('Upload a file (max 50MB) for use with RAG or context.')}
							</div>
							<div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
								<pre class="font-mono text-xs px-2 py-1 overflow-x-auto whitespace-pre-wrap">curl -X POST https://llm.oriagent.com/api/public/v1/files \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "purpose=rag"</pre>
							</div>
						</div>

						<!-- Audio API -->
						<div class="space-y-4">
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300">
								{$i18n.t('Audio Processing')}
							</div>
							
							<div>
								<div class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-2">
									<span class="font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded text-[10px]">POST</span>
									/audio/transcriptions <span class="text-gray-400 font-normal ml-1">({$i18n.t('Speech to Text')})</span>
								</div>
								<div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
									<pre class="font-mono text-xs px-2 py-1 overflow-x-auto whitespace-pre-wrap">curl -X POST https://llm.oriagent.com/api/public/v1/audio/transcriptions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@audio.mp3" -F "language=en"</pre>
								</div>
							</div>

							<div>
								<div class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-2">
									<span class="font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded text-[10px]">POST</span>
									/audio/speech <span class="text-gray-400 font-normal ml-1">({$i18n.t('Text to Speech')})</span>
								</div>
								<div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
									<pre class="font-mono text-xs px-2 py-1 overflow-x-auto whitespace-pre-wrap">curl -X POST https://llm.oriagent.com/api/public/v1/audio/speech \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '&#123;"input": "Hello, I am OriAgent."&#125;' --output speech.mp3</pre>
								</div>
							</div>
						</div>

						<!-- Knowledge Query -->
						<div>
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2">
								<span class="font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded text-[10px]">POST</span>
								/knowledge/query
							</div>
							<div class="text-xs text-gray-500 dark:text-gray-400 mb-2">
								{$i18n.t('Query a specific knowledge base using RAG.')}
							</div>
							<div class="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
								<pre class="font-mono text-xs px-2 py-1 overflow-x-auto whitespace-pre-wrap">curl -X POST https://llm.oriagent.com/api/public/v1/knowledge/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '&#123;
    "knowledge_id": "your-knowledge-id",
    "query": "What is the policy?",
    "top_k": 3
  &#125;'</pre>
							</div>
						</div>

						<!-- Other Endpoints List -->
						<div>
							<div class="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
								{$i18n.t('Other Available Endpoints')}
							</div>
							<div class="text-xs space-y-1.5">
								<div class="flex items-center gap-2">
									<span class="font-mono bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-1.5 py-0.5 rounded text-[10px]">GET</span>
									<span class="font-mono">/health</span>
									<span class="text-gray-400 hidden sm:inline">— {$i18n.t('Health check (No Auth)')}</span>
								</div>
								<div class="flex items-center gap-2">
									<span class="font-mono bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-1.5 py-0.5 rounded text-[10px]">GET</span>
									<span class="font-mono">/models</span>
									<span class="text-gray-400 hidden sm:inline">— {$i18n.t('List available models')}</span>
								</div>
								<div class="flex items-center gap-2">
									<span class="font-mono bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-1.5 py-0.5 rounded text-[10px]">GET</span>
									<span class="font-mono">/files/&#123;id&#125;</span>
									<span class="text-gray-400 hidden sm:inline">— {$i18n.t('Get file metadata')}</span>
								</div>
								<div class="flex items-center gap-2">
									<span class="font-mono bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 px-1.5 py-0.5 rounded text-[10px]">DEL</span>
									<span class="font-mono">/files/&#123;id&#125;</span>
									<span class="text-gray-400 hidden sm:inline">— {$i18n.t('Delete a file')}</span>
								</div>
								<div class="flex items-center gap-2">
									<span class="font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 px-1.5 py-0.5 rounded text-[10px]">POST</span>
									<span class="font-mono">/images/generations</span>
									<span class="text-gray-400 hidden sm:inline">— {$i18n.t('Generate images from text')}</span>
								</div>
							</div>
						</div>
					</div>
				</div>
		{:else}
			<div class="mt-5 text-center py-8">
				<div class="text-gray-400 animate-pulse">{$i18n.t('Loading...')}</div>
			</div>
		{/if}
	</div>
</div>
