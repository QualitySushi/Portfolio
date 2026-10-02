<script lang="ts">
  import { onMount } from 'svelte';
  import { trackEvent } from '../lib/utils/telemetry';

  // Portfolio state and navigation
  let activeTab = $state<'overview' | 'experience' | 'projects'>('overview');

  // Track initial page view on mount
  onMount(() => {
    trackEvent('page_view', { tab: activeTab });
  });

  // Handle tab switches with telemetry logging
  function handleTabChange(tab: 'overview' | 'experience' | 'projects') {
    activeTab = tab;
    trackEvent('tab_switch', { target_tab: tab });
  }

  // Handle project exploration clicks
  function handleProjectClick(projectTitle: string, link: string) {
    trackEvent('project_click', { project_title: projectTitle, destination: link });
  }

  const projects = [
    {
      title: "Efficiency Estimator Suite",
      description: "Full-stack photovoltaic module simulation platform with headless FastAPI modeling, Supabase telemetry, and interactive SvelteKit batch optimization—primarily engineered independently with group unit testing support.",
      tags: ["Python", "FastAPI", "SvelteKit", "Supabase", "pvlib"],
      link: "/ee-playground"
    },
    {
      title: "G-Code Generator & Rotation Suite",
      description: "PyQt6 desktop application designed to generate, preview, and export laser scribing/CNC instructions for solar panel cell arrays, featuring modular architecture and live QGraphicsView rendering.",
      tags: ["Python", "PyQt6", "QGraphicsView", "Architecture Design"],
      link: "/gg-playground"
    },
    {
      title: "PokeBrain AI",
      description: "Modular AI pipeline designed for training intelligent agents on Pokémon battle mechanics, featuring replay parsing and synthetic state generation.",
      tags: ["Python", "Machine Learning", "PyTorch", "Architecture Design"],
      link: "https://github.com/QualitySushi"
    },
    {
      title: "Atlas Framework",
      description: "Modular software engineering scaffolding and project template system designed to streamline multi-stack web, desktop, and server development.",
      tags: ["TypeScript", "Svelte", "Node.js", "Architecture"],
      link: "https://github.com/QualitySushi/Atlas"
    }
  ];

  const experiences = [
    {
      role: "Solar Engineering Software Developer (Capstone & Internship)",
      company: "Collaborative Solar Processing Initiative",
      period: "Graduation 2026",
      description: "Contributed to a comprehensive solar engineering initiative encompassing two key deliverables. Collaborated with cohort peers on the core PyQt6 G-Code Generator and Rotation pipeline for laser scribing operations, and independently spearheaded the design and development of the advanced photovoltaic Efficiency Estimator simulation suite."
    },
    {
      role: "Engineering & Field Construction",
      company: "Formwork Construction & Labor",
      period: "Multiple Years",
      description: "Applied rigorous safety standards (WHMIS) and precision execution in heavy formwork construction. Developed strong structural problem-solving skills, physical systems intuition, and team coordination under high-demand environments."
    }
  ];
</script>

<div class="min-h-screen bg-gray-50 text-gray-800">
  <!-- Navigation Header -->
  <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
      <div class="flex items-center space-x-3">
        <span class="text-xl font-bold bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
          Software & Systems Engineering
        </span>
      </div>
      <nav class="flex space-x-6">
        <button 
          class="text-sm font-medium transition-colors hover:text-blue-600 {activeTab === 'overview' ? 'text-blue-600 border-b-2 border-blue-600 pb-1' : 'text-gray-600'}"
          onclick={() => handleTabChange('overview')}
        >
          Overview
        </button>
        <button 
          class="text-sm font-medium transition-colors hover:text-blue-600 {activeTab === 'experience' ? 'text-blue-600 border-b-2 border-blue-600 pb-1' : 'text-gray-600'}"
          onclick={() => handleTabChange('experience')}
        >
          Experience
        </button>
        <button 
          class="text-sm font-medium transition-colors hover:text-blue-600 {activeTab === 'projects' ? 'text-blue-600 border-b-2 border-blue-600 pb-1' : 'text-gray-600'}"
          onclick={() => handleTabChange('projects')}
        >
          Projects
        </button>
      </nav>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="max-w-7xl mx-auto px-4 py-16 lg:py-24">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
      <div class="lg:col-span-7 space-y-6">
        <div class="inline-block bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">
          Software Engineering Graduate • Halifax, NS
        </div>
        <h1 class="text-4xl lg:text-6xl font-extrabold text-gray-900 tracking-tight">
          Bridging physical systems & <span class="text-blue-600">robust software architecture.</span>
        </h1>
        <p class="text-lg text-gray-600 leading-relaxed">
          I build modular software frameworks, high-performance simulation microservices, and reactive user interfaces. Combining years of hands-on physical engineering discipline with modern full-stack development.
        </p>
        <div class="flex space-x-4 pt-2">
          <a 
            href="https://github.com/QualitySushi" 
            target="_blank" 
            rel="noreferrer"
            onclick={() => trackEvent('external_link_click', { destination: 'https://github.com/QualitySushi', context: 'hero_github' })}
            class="bg-white border border-gray-300 text-gray-700 font-medium px-6 py-3 rounded-xl shadow-sm hover:bg-gray-50 transition"
          >
            GitHub Repositories
          </a>
        </div>
      </div>

      <!-- Quick Stats / Highlights Card -->
      <div class="lg:col-span-5 bg-white p-8 rounded-2xl shadow-xl border border-gray-100 space-y-6">
        <h3 class="text-xl font-bold text-gray-900 border-b pb-4">Core Competencies</h3>
        <ul class="space-y-4 text-sm text-gray-700">
          <li class="flex items-start space-x-3">
            <span class="text-blue-600 font-bold">✓</span>
            <div>
              <strong class="text-gray-900">Full-Stack Architecture:</strong> SvelteKit, FastAPI, Node.js, Express, and PostgreSQL/Supabase.
            </div>
          </li>
          <li class="flex items-start space-x-3">
            <span class="text-blue-600 font-bold">✓</span>
            <div>
              <strong class="text-gray-900">Desktop & GUI Engineering:</strong> Standalone Python/Qt & PyQt6 application design.
            </div>
          </li>
          <li class="flex items-start space-x-3">
            <span class="text-blue-600 font-bold">✓</span>
            <div>
              <strong class="text-gray-900">Simulation & Algorithms:</strong> Numerical modeling pipelines (`pvlib`), AI agent architectures, and data processing.
            </div>
          </li>
          <li class="flex items-start space-x-3">
            <span class="text-blue-600 font-bold">✓</span>
            <div>
              <strong class="text-gray-900">Field & Structural Discipline:</strong> Practical heavy construction experience emphasizing precision and safety standards.
            </div>
          </li>
        </ul>
      </div>
    </div>
  </section>

  <!-- Dynamic Content Section Based on Tabs -->
  <section class="max-w-7xl mx-auto px-4 pb-24">
    {#if activeTab === 'overview' || activeTab === 'projects'}
      <div class="mb-12">
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Featured Projects & Systems</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          {#each projects as project}
            <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition flex flex-col justify-between">
              <div>
                <h3 class="text-lg font-bold text-gray-900 mb-2">{project.title}</h3>
                <p class="text-gray-600 text-sm mb-4 leading-relaxed">{project.description}</p>
                <div class="flex flex-wrap gap-2 mb-6">
                  {#each project.tags as tag}
                    <span class="bg-gray-100 text-gray-700 text-xs font-medium px-2.5 py-1 rounded-md">{tag}</span>
                  {/each}
                </div>
              </div>
              <a 
                href={project.link} 
                onclick={() => handleProjectClick(project.title, project.link)}
                class="text-blue-600 font-medium text-sm hover:underline inline-flex items-center space-x-1"
              >
                <span>Explore Project</span>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
              </a>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if activeTab === 'overview' || activeTab === 'experience'}
      <div>
        <h2 class="text-2xl font-bold text-gray-900 mb-6">Professional & Field Experience</h2>
        <div class="space-y-6">
          {#each experiences as exp}
            <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
              <div class="flex flex-col md:flex-row md:justify-between md:items-center mb-3">
                <h3 class="text-lg font-bold text-gray-900">{exp.role} <span class="text-blue-600 font-normal">({exp.company})</span></h3>
                <span class="text-xs font-semibold bg-blue-50 text-blue-700 px-3 py-1 rounded-full w-fit mt-1 md:mt-0">{exp.period}</span>
              </div>
              <p class="text-gray-600 text-sm leading-relaxed">{exp.description}</p>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </section>

  <!-- Footer -->
  <footer class="bg-white border-t border-gray-200 py-8 text-center text-sm text-gray-500">
    <p>© 2026 Software Engineering Portfolio. Built with SvelteKit, FastAPI, and Tailwind CSS.</p>
  </footer>
</div>