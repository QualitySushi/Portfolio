<script lang="ts">
  import ParameterForm from '../../lib/components/generator/ParameterForm.svelte';
  import OutputTerminal from '../../lib/components/generator/OutputTerminal.svelte';
  import PathVisualizer from '../../lib/components/generator/PathVisualizer.svelte';
  import HistoryView from '../../lib/components/generator/HistoryView.svelte';

  // State declared correctly with Svelte 5 $state runes
  let loading = $state(false);
  let saving = $state(false);
  let outputResult = $state('');
  let errorMessage = $state('');
  let saveMessage = $state('');
  let lastPayload = $state<any>(null);

  async function handleGenerate(payload: any) {
    loading = true;
    saving = false;
    errorMessage = '';
    saveMessage = '';
    outputResult = '';
    lastPayload = payload;

    console.group('[GG-Playground] Generation Pipeline Triggered');
    console.log('Outgoing Payload:', payload);

    try {
      const endpoint = 'http://localhost:4000/api/gcode/generate';
      console.log(`Sending POST request to: ${endpoint}`);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      console.log(`Response Received — Status: ${response.status} ${response.statusText}`);

      const rawText = await response.text();
      let data;

      try {
        data = JSON.parse(rawText);
        console.log('Successfully Parsed JSON:', data);
      } catch (parseError) {
        console.error('JSON Parsing Failed. The server may have returned HTML or plain text instead of JSON.');
        throw new Error(
          `Server returned non-JSON response (${response.status}): ${rawText.slice(0, 100)}...`
        );
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
          data.error ||
          `Server responded with status ${response.status}`
        );
      }

      outputResult = data.output;
      console.log('Output successfully assigned to terminal.');
    } catch (err: any) {
      console.error('Generation Workflow Error:', err);
      errorMessage = err.message || 'An unexpected error occurred.';
    } finally {
      loading = false;
      console.groupEnd();
    }
  }

  async function handleSaveToDb() {
    if (!outputResult || !lastPayload) return;

    saving = true;
    saveMessage = '';

    try {
      const endpoint = 'http://localhost:4000/api/gcode/save';
      console.log(`Sending save request to: ${endpoint}`);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: lastPayload.user_id || 'user_demo_123',
          file_type: lastPayload.file_type,
          output_data: outputResult
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to save to database');
      }

      saveMessage = 'Successfully saved to database!';
    } catch (err: any) {
      console.error('Save Workflow Error:', err);
      saveMessage = `Error: ${err.message}`;
    } finally {
      saving = false;
    }
  }
</script>

<main class="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12 font-sans">
  <div class="max-w-6xl mx-auto space-y-8">

    <header class="border-b border-slate-800 pb-4 flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight text-indigo-400">
          GG-Playground
        </h1>

        <p class="text-slate-400 text-sm mt-1">
          Interactive Laser Scriber Path Planning & G-Code Generation Workbench
        </p>
      </div>

      <div class="text-xs px-3 py-1 bg-slate-900 border border-slate-700 rounded-full text-emerald-400">
        ● Gateway Connected
      </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <div class="lg:col-span-5">
        <ParameterForm {loading} onGenerate={handleGenerate} />
      </div>

      <div class="lg:col-span-7 flex flex-col space-y-4">
        <!-- Live Visualizer Component -->
        <PathVisualizer {outputResult} />

        <OutputTerminal
          {outputResult}
          {errorMessage}
          {loading}
        />

        {#if outputResult}
          <div class="flex items-center justify-between bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-lg">
            <div>
              <p class="text-sm font-medium text-slate-300">
                Database Action
              </p>

              <p class="text-xs text-slate-400">
                Manually save this generation output to your Supabase history.
              </p>

              {#if saveMessage}
                <p
                  class="text-xs mt-1 font-semibold {saveMessage.includes('Successfully')
                    ? 'text-emerald-400'
                    : 'text-red-400'}"
                >
                  {saveMessage}
                </p>
              {/if}
            </div>

            <button
              onclick={handleSaveToDb}
              disabled={saving}
              class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-sm rounded-lg transition-colors flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed shrink-0"
            >
              {#if saving}
                <span>⏳</span> Saving...
              {:else}
                Save to Database
              {/if}
            </button>
          </div>
        {/if}
      </div>
    </div>

    <!-- Generation History -->
    <section>
      <HistoryView
        userId={lastPayload?.user_id || 'user_demo_123'}
      />
    </section>

  </div>
</main>