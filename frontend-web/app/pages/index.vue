<template>
  <WavyBackground>
    <main class="relative text-surface-100 overflow-hidden min-h-screen flex flex-col">

      <header class="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between w-full border-b border-surface-800/50 bg-surface-950/40 backdrop-blur-sm">
        <!-- Brand -->
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-[0_0_15px_rgba(var(--color-brand-600),0.5)]">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <span class="text-lg font-bold tracking-tight text-white">MailShield AI</span>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <template v-if="authenticated">
            <div class="flex items-center gap-4">
              <InteractiveHoverButton 
                id="btn-logout" 
                class="!border-transparent !bg-transparent hover:!border-surface-700 text-surface-200"
                @click="handleLogout"
              >
                Sign out
              </InteractiveHoverButton>

              <!-- Profile Logo -->
              <div v-if="userPicture" class="w-9 h-9 rounded-full overflow-hidden border border-surface-700 shadow-lg">
                <img :src="userPicture" alt="Profile" class="w-full h-full object-cover" />
              </div>
              <div v-else class="w-9 h-9 rounded-full bg-gradient-to-tr from-brand-500 to-purple-500 flex items-center justify-center text-white shadow-lg border border-surface-700">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </template>
          <template v-else>
            <InteractiveHoverButton
              class="!bg-white/10 hover:!bg-white/20 border-white/10 !text-white shadow-none backdrop-blur-md"
              @click="handleSignIn"
              :disabled="loading"
              :text="loading ? 'Connecting...' : 'Sign In'"
            />
          </template>
        </div>
      </header>


      <!-- Landing Page Content -->
      <div class="flex-1 flex flex-col relative z-10">
        <!-- Hero Section -->

      <section class="relative z-10 pt-24 pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col items-center text-center">
        <div 
          v-motion :initial="fadeUp(0).initial" :enter="fadeUp(0).enter"
          class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-900/30 border border-brand-800/50 text-brand-300 text-sm font-medium mb-8"
        >
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
          </span>
          Machine Learning Powered Security
        </div>
        
        <h1 
          v-motion :initial="fadeUp(150).initial" :enter="fadeUp(150).enter"
          class="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-transparent bg-clip-text bg-gradient-to-b from-white to-surface-400 max-w-4xl"
        >
          Intelligent threat detection for your inbox.
        </h1>
        
        <p 
          v-motion :initial="fadeUp(300).initial" :enter="fadeUp(300).enter"
          class="text-lg md:text-xl text-surface-400 max-w-2xl mb-12 leading-relaxed"
        >
          MailShield AI scans your Gmail using an advanced LinearSVC machine learning model to automatically categorize emails, block phishing attempts, and keep your inbox secure.
        </p>
        
        <div 
          v-motion :initial="fadeUp(450).initial" :enter="fadeUp(450).enter"
          class="flex flex-col sm:flex-row gap-4 items-center w-full justify-center max-w-md"
        >
          <ShimmerButton
            v-if="!authenticated"
            class="w-full sm:w-auto shadow-2xl"
            shimmer-color="rgba(255, 255, 255, 0.4)"
            shimmer-size="2px"
            border-radius="100px"
            shimmer-duration="3s"
            background="#000000"
            @click="handleSignIn"
            :disabled="loading"
          >
            <span class="flex items-center gap-2 text-white font-semibold text-lg whitespace-nowrap">
              {{ loading ? 'Connecting...' : 'Secure Your Inbox' }}
            </span>
          </ShimmerButton>
          <ShimmerButton
            v-else
            class="w-full sm:w-auto shadow-2xl"
            shimmer-color="rgba(255, 255, 255, 0.4)"
            shimmer-size="2px"
            border-radius="100px"
            shimmer-duration="3s"
            background="#000000"
            @click="handleHeroAction"
          >
            <span class="flex items-center gap-2 text-white font-semibold text-lg whitespace-nowrap">
              Secure Your Inbox
            </span>
          </ShimmerButton>
        </div>
        
        <p v-if="error" class="mt-6 text-sm text-red-400 bg-red-950/50 border border-red-900/50 px-4 py-2 rounded-lg max-w-md mx-auto">
          {{ error }}
        </p>
        <p class="mt-6 text-xs text-surface-500 max-w-sm">
          We only request <span class="text-surface-300">gmail.modify</span> & <span class="text-surface-300">gmail.labels</span>. We never store your emails.
        </p>
      </section>

      <!-- Try It Section -->
      <section class="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-32">
        <div 
          v-motion :initial="fadeUp(300).initial" :visible-once="fadeUp(300).enter"
          class="bg-surface-900/40 backdrop-blur-xl border border-surface-700/50 p-6 sm:p-8 rounded-3xl shadow-2xl relative overflow-hidden"
        >
          <!-- Decorative blob -->
          <div class="absolute -top-24 -right-24 w-48 h-48 bg-brand-500/20 rounded-full blur-3xl pointer-events-none"></div>
          <div class="absolute -bottom-24 -left-24 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl pointer-events-none"></div>
          
          <div class="relative z-10">
            <div class="text-center mb-6">
              <h2 class="text-2xl sm:text-3xl font-bold text-white mb-2">Try it right now</h2>
              <p class="text-surface-400">Paste a suspicious email or message below to see our ML model in action.</p>
            </div>
            
            <div class="relative group">
              <textarea
                v-model="tryItText"
                rows="4"
                placeholder="Paste message content here..."
                class="w-full bg-surface-950/50 border border-surface-700 rounded-2xl p-4 text-white placeholder:text-surface-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 transition-all resize-none"
                :disabled="tryItLoading"
              ></textarea>
              
              <div class="mt-4 flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div class="text-sm min-h-[48px] flex items-center">
                  <!-- Result display -->
                  <transition name="fade" mode="out-in">
                    <div v-if="tryItResult" class="flex items-center gap-3 bg-surface-800/80 px-4 py-2 rounded-xl border border-surface-700">
                      <span 
                        class="flex items-center justify-center w-8 h-8 rounded-full"
                        :class="tryItResult.label === 'spam' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'"
                      >
                        <svg v-if="tryItResult.label === 'spam'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                        <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      </span>
                      <div>
                        <div class="font-semibold" :class="tryItResult.label === 'spam' ? 'text-red-400' : 'text-emerald-400'">
                          {{ tryItResult.label === 'spam' ? 'Spam Detected' : 'Looks Safe' }}
                        </div>
                        <div class="text-xs text-surface-400">
                          Confidence: {{ (tryItResult.confidence * 100).toFixed(1) }}%
                        </div>
                      </div>
                      <button @click="clearTryIt" class="ml-2 text-surface-500 hover:text-white transition-colors" title="Clear">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>
                    <div v-else-if="tryItError" class="text-red-400 text-sm bg-red-950/30 px-4 py-2 rounded-xl border border-red-900/50">
                      {{ tryItError }}
                    </div>
                  </transition>
                </div>
                
                <InteractiveHoverButton
                  :text="tryItLoading ? 'Analyzing...' : 'Analyze Message'"
                  :disabled="tryItLoading || !tryItText.trim()"
                  @click="handleTryIt"
                  class="w-full sm:w-auto"
                  :class="{ 'opacity-50 cursor-not-allowed': tryItLoading || !tryItText.trim() }"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Features Grid -->
      <section class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          <!-- Feature 1 -->
          <div 
            v-motion :initial="fadeUp(0).initial" :visible-once="fadeUp(0).enter"
            class="bg-surface-900/50 backdrop-blur-md border border-surface-800 p-8 rounded-2xl hover:bg-surface-800/50 transition-colors duration-300 group"
          >
            <div class="w-12 h-12 rounded-xl bg-red-950/50 border border-red-900/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <svg class="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Threat Mitigation</h3>
            <p class="text-surface-400 leading-relaxed text-sm">
              Instantly flags <span class="text-red-400 font-medium">Phishing</span> and <span class="text-amber-400 font-medium">Spam</span> attempts with deep textual analysis and TF-IDF vectorization.
            </p>
          </div>

          <!-- Feature 2 -->
          <div 
            v-motion :initial="fadeUp(150).initial" :visible-once="fadeUp(150).enter"
            class="bg-surface-900/50 backdrop-blur-md border border-surface-800 p-8 rounded-2xl hover:bg-surface-800/50 transition-colors duration-300 group"
          >
            <div class="w-12 h-12 rounded-xl bg-blue-950/50 border border-blue-900/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <svg class="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002 2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Smart Categorization</h3>
            <p class="text-surface-400 leading-relaxed text-sm">
              Automatically sorts your inbox into 11 distinct labels including <span class="text-cyan-400 font-medium">Work</span>, <span class="text-teal-400 font-medium">Banking</span>, <span class="text-orange-400 font-medium">Promotions</span>, and <span class="text-purple-400 font-medium">Orders</span>.
            </p>
          </div>

          <!-- Feature 3 -->
          <div 
            v-motion :initial="fadeUp(300).initial" :visible-once="fadeUp(300).enter"
            class="bg-surface-900/50 backdrop-blur-md border border-surface-800 p-8 rounded-2xl hover:bg-surface-800/50 transition-colors duration-300 group"
          >
            <div class="w-12 h-12 rounded-xl bg-brand-950/50 border border-brand-900/50 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <svg class="w-6 h-6 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-white mb-3">Live Processing</h3>
            <p class="text-surface-400 leading-relaxed text-sm">
              Watch the ML model process your inbox in real-time. Server-Sent Events stream scan progress directly to a sleek terminal interface.
            </p>
          </div>

        </div>
      </section>

      <!-- Pipeline Information Section -->
      <section class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-32">
        <div 
          v-motion :initial="fadeUp(0).initial" :visible-once="fadeUp(0).enter"
          class="text-center mb-16 md:mb-24"
        >
          <h2 class="text-3xl sm:text-4xl font-bold text-white mb-4">How it works</h2>
          <p class="text-surface-400 max-w-2xl mx-auto">MailShield AI uses a sophisticated ML pipeline to analyze, categorize, and secure your inbox in real-time.</p>
        </div>

        <div class="relative flex flex-col items-center">
          <!-- Animated connecting line (desktop) -->
          <div class="hidden md:block absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-brand-500/50 to-transparent -translate-x-1/2"></div>
          
          <!-- Animated connecting line (mobile) -->
          <div class="block md:hidden absolute left-8 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-brand-500/50 to-transparent"></div>

          <!-- Step 1: Extraction -->
          <div 
            v-motion :initial="fadeUp(100).initial" :visible-once="fadeUp(100).enter"
            class="relative w-full flex flex-col md:flex-row items-center justify-between mb-16 md:mb-24 group"
          >
            <div class="hidden md:block w-5/12 text-right pr-12">
              <h3 class="text-2xl font-bold text-white mb-3 group-hover:text-brand-400 transition-colors">1. Secure Extraction</h3>
              <p class="text-surface-400 text-sm leading-relaxed">Connects to the Gmail API using read-only scopes. We fetch email headers and decode the body while ensuring strict privacy. Emails are never stored.</p>
            </div>
            <div class="absolute left-8 md:left-1/2 w-12 h-12 bg-surface-950 border border-brand-500/50 rounded-full flex items-center justify-center -translate-x-1/2 z-10 shadow-[0_0_20px_rgba(var(--color-brand-600),0.3)] group-hover:border-brand-400 group-hover:shadow-[0_0_30px_rgba(var(--color-brand-500),0.6)] group-hover:scale-110 transition-all duration-500">
              <svg class="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
            </div>
            <div class="w-full md:w-5/12 pl-20 md:pl-12">
              <div class="block md:hidden mb-4">
                <h3 class="text-xl font-bold text-white group-hover:text-brand-400 transition-colors">1. Secure Extraction</h3>
                <p class="text-surface-400 text-sm leading-relaxed mt-2">Connects to the Gmail API using read-only scopes. We fetch email headers and decode the body while ensuring strict privacy.</p>
              </div>
              <div class="bg-surface-900/40 backdrop-blur-md border border-surface-800 p-5 rounded-2xl shadow-lg relative overflow-hidden group-hover:border-brand-500/30 transition-colors duration-500">
                <div class="absolute inset-0 bg-gradient-to-r from-brand-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <pre class="font-mono text-xs text-surface-300 overflow-x-auto"><code>GET /gmail/v1/users/me/messages
Headers: Authorization: Bearer...
Response: { "id": "189a...", "snippet": "..." }</code></pre>
              </div>
            </div>
          </div>

          <!-- Step 2: Preprocessing -->
          <div 
            v-motion :initial="fadeUp(100).initial" :visible-once="fadeUp(100).enter"
            class="relative w-full flex flex-col md:flex-row-reverse items-center justify-between mb-16 md:mb-24 group"
          >
            <div class="hidden md:block w-5/12 text-left pl-12">
              <h3 class="text-2xl font-bold text-white mb-3 group-hover:text-purple-400 transition-colors">2. Preprocessing & NLP</h3>
              <p class="text-surface-400 text-sm leading-relaxed">Raw text is cleaned, tokenized, and converted to lowercase. URLs, emails, and numbers are replaced with special tokens before TF-IDF vectorization transforms the text into an ML-ready numerical matrix.</p>
            </div>
            <div class="absolute left-8 md:left-1/2 w-12 h-12 bg-surface-950 border border-purple-500/50 rounded-full flex items-center justify-center -translate-x-1/2 z-10 shadow-[0_0_20px_rgba(168,85,247,0.3)] group-hover:border-purple-400 group-hover:shadow-[0_0_30px_rgba(168,85,247,0.6)] group-hover:scale-110 transition-all duration-500">
              <svg class="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
            </div>
            <div class="w-full md:w-5/12 pl-20 md:pr-12 md:pl-0">
              <div class="block md:hidden mb-4">
                <h3 class="text-xl font-bold text-white group-hover:text-purple-400 transition-colors">2. Preprocessing & NLP</h3>
                <p class="text-surface-400 text-sm leading-relaxed mt-2">Raw text is cleaned, tokenized, and converted to lowercase. URLs, emails, and numbers are replaced with special tokens.</p>
              </div>
              <div class="bg-surface-900/40 backdrop-blur-md border border-surface-800 p-5 rounded-2xl shadow-lg relative overflow-hidden group-hover:border-purple-500/30 transition-colors duration-500">
                 <div class="absolute inset-0 bg-gradient-to-l from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                 <pre class="font-mono text-xs text-surface-300 overflow-x-auto"><code>text = clean_text(email.body)
vector = tfidf.transform([text])
# Shape: (1, 15000) sparse matrix</code></pre>
              </div>
            </div>
          </div>

          <!-- Step 3: ML Classification -->
          <div 
            v-motion :initial="fadeUp(100).initial" :visible-once="fadeUp(100).enter"
            class="relative w-full flex flex-col md:flex-row items-center justify-between mb-16 md:mb-24 group"
          >
            <div class="hidden md:block w-5/12 text-right pr-12">
              <h3 class="text-2xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">3. LinearSVC Classification</h3>
              <p class="text-surface-400 text-sm leading-relaxed">The high-dimensional sparse matrix is passed to our fine-tuned Linear Support Vector Classifier (LinearSVC). The model calculates decision scores across 11 distinct categories to find the perfect match.</p>
            </div>
            <div class="absolute left-8 md:left-1/2 w-12 h-12 bg-surface-950 border border-blue-500/50 rounded-full flex items-center justify-center -translate-x-1/2 z-10 shadow-[0_0_20px_rgba(59,130,246,0.3)] group-hover:border-blue-400 group-hover:shadow-[0_0_30px_rgba(59,130,246,0.6)] group-hover:scale-110 transition-all duration-500">
              <svg class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>
            </div>
            <div class="w-full md:w-5/12 pl-20 md:pl-12">
              <div class="block md:hidden mb-4">
                <h3 class="text-xl font-bold text-white group-hover:text-blue-400 transition-colors">3. LinearSVC Classification</h3>
                <p class="text-surface-400 text-sm leading-relaxed mt-2">The sparse matrix is passed to our Linear Support Vector Classifier, calculating decision scores across 11 distinct categories.</p>
              </div>
              <div class="bg-surface-900/40 backdrop-blur-md border border-surface-800 p-5 rounded-2xl shadow-lg relative overflow-hidden group-hover:border-blue-500/30 transition-colors duration-500">
                <div class="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <pre class="font-mono text-xs text-surface-300 overflow-x-auto"><code>scores = model.decision_function(vector)
prediction = classes[np.argmax(scores)]
confidence = softmax(scores)</code></pre>
              </div>
            </div>
          </div>

          <!-- Step 4: Action -->
          <div 
            v-motion :initial="fadeUp(100).initial" :visible-once="fadeUp(100).enter"
            class="relative w-full flex flex-col md:flex-row-reverse items-center justify-between group"
          >
            <div class="hidden md:block w-5/12 text-left pl-12">
              <h3 class="text-2xl font-bold text-white mb-3 group-hover:text-emerald-400 transition-colors">4. Smart Action & Labeling</h3>
              <p class="text-surface-400 text-sm leading-relaxed">The predicted label (e.g., Spam, Phishing, Orders) is mapped to a Gmail Label ID. The API applies this label to the email, organizing your inbox instantly.</p>
            </div>
            <div class="absolute left-8 md:left-1/2 w-12 h-12 bg-surface-950 border border-emerald-500/50 rounded-full flex items-center justify-center -translate-x-1/2 z-10 shadow-[0_0_20px_rgba(16,185,129,0.3)] group-hover:border-emerald-400 group-hover:shadow-[0_0_30px_rgba(16,185,129,0.6)] group-hover:scale-110 transition-all duration-500">
              <svg class="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            </div>
            <div class="w-full md:w-5/12 pl-20 md:pr-12 md:pl-0">
              <div class="block md:hidden mb-4">
                <h3 class="text-xl font-bold text-white group-hover:text-emerald-400 transition-colors">4. Smart Action & Labeling</h3>
                <p class="text-surface-400 text-sm leading-relaxed mt-2">The predicted label is mapped to a Gmail Label ID and applied to the email, organizing your inbox instantly.</p>
              </div>
              <div class="bg-surface-900/40 backdrop-blur-md border border-surface-800 p-5 rounded-2xl shadow-lg relative overflow-hidden group-hover:border-emerald-500/30 transition-colors duration-500">
                <div class="absolute inset-0 bg-gradient-to-l from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <pre class="font-mono text-xs text-surface-300 overflow-x-auto"><code>POST /gmail/v1/users/me/messages/{id}/modify
{
  "addLabelIds": ["Label_4"],
  "removeLabelIds": ["INBOX"]
}</code></pre>
              </div>
            </div>
          </div>

        </div>
      </section>

      
        <!-- Footer -->

      <footer class="relative z-10 border-t border-surface-800 py-8 text-center text-surface-500 text-sm">
        <p>Powered by Vue 3, FastAPI, and LinearSVC.</p>
      </footer>
    
      </div>

      <!-- Authenticated View (Dashboard) -->
      <div v-if="authenticated" id="dashboard" class="flex-1 flex flex-col relative z-10 min-h-screen">

    <main class="flex-1 w-full max-w-[95%] xl:max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">

      <!-- Error banner -->
      <div v-if="scanError" class="mb-6 card border-red-900 bg-red-950/30 flex items-start gap-3 !p-4">
        <svg class="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
          <p class="text-sm font-medium text-red-300">Scan Error</p>
          <p class="text-sm text-red-400 mt-0.5">{{ scanError }}</p>
        </div>
        <button class="ml-auto btn-ghost !p-1 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-red-600 focus-visible:ring-offset-surface-950" @click="scanError = null">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Scanning Live Terminal State -->
      <div v-if="scanning" class="mb-8 relative z-10">
        <div class="card border-surface-700 shadow-2xl !p-8 flex flex-col gap-6 w-full max-w-3xl mx-auto">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="relative">
                <div class="w-10 h-10 rounded-full border-2 border-surface-800 border-t-brand-500 animate-spin" />
              </div>
              <div>
                <p class="text-base font-medium text-surface-100">Scanning your inbox…</p>
                <p class="text-muted text-sm mt-0.5">Fetching emails, running ML model, and applying labels.</p>
              </div>
            </div>
            
            <div class="flex items-center gap-6 text-right tabular-nums">
              <button
                v-if="!stopping"
                class="btn-ghost !text-red-400 hover:!text-red-300 hover:!bg-red-950/50 !px-4 !py-2 text-sm font-medium border border-red-900/30 rounded-lg"
                @click="handleStopScan"
              >
                Stop Scan
              </button>
              <span v-else class="text-surface-500 text-sm font-medium animate-pulse">Stopping...</span>
              
              <div>
                <p class="text-2xl font-semibold text-surface-100">
                  <span class="text-brand-400">{{ scanProgress.current }}</span>
                  <span class="text-surface-500 text-lg"> / {{ scanProgress.total || '?' }}</span>
                </p>
                <p class="text-muted text-xs uppercase tracking-wider mt-1">Processed</p>
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="w-full h-2 bg-surface-800 rounded-full overflow-hidden">
            <div 
              class="h-full bg-brand-500 transition-all duration-300 ease-out"
              :style="{ width: scanProgress.total > 0 ? `${(scanProgress.current / scanProgress.total) * 100}%` : '0%' }"
            ></div>
          </div>

          <!-- Terminal -->
          <div class="bg-black/80 border border-surface-800 rounded-lg p-4 font-mono text-xs overflow-y-auto h-64 shadow-inner" ref="terminalEl">
            <div 
              v-for="(log, idx) in scanLogs" :key="idx" 
              class="text-surface-300 whitespace-pre-wrap leading-relaxed animate-fade-in"
            >
              <span class="text-surface-500 select-none mr-2">❯</span>{{ log }}
            </div>
            <!-- Blinking cursor -->
            <div class="text-surface-500 mt-1 animate-pulse">_</div>
          </div>
        </div>
        
        <!-- Skeleton Loader (Shown while waiting for results) -->
        <div v-if="results.length === 0" class="mt-8 max-w-7xl mx-auto card border-surface-700 !p-0 overflow-hidden relative z-10">
          <div class="w-full">
            <div class="px-4 py-3 border-b border-surface-800 bg-surface-900/50 flex gap-4">
              <div class="h-3 w-64 bg-surface-800 rounded animate-pulse"></div>
              <div class="h-3 flex-1 bg-surface-800 rounded animate-pulse"></div>
              <div class="h-3 w-48 hidden sm:block bg-surface-800 rounded animate-pulse"></div>
            </div>
            <div v-for="i in 5" :key="i" class="px-4 py-4 border-b border-surface-800/50 flex gap-4">
              <div class="h-4 w-48 bg-surface-800/50 rounded animate-pulse"></div>
              <div class="h-4 flex-1 bg-surface-800/50 rounded animate-pulse"></div>
              <div class="h-5 w-24 hidden sm:block bg-surface-800/50 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state (not yet scanned) -->
      <div v-else-if="!results.length && !scanError" class="animate-fade-in">
        <div class="card !p-12 flex flex-col items-center gap-4 text-center max-w-lg mx-auto">
          <div class="w-14 h-14 rounded-2xl bg-surface-800 flex items-center justify-center">
            <svg class="w-7 h-7 text-surface-500" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <div>
            <p class="text-base font-medium text-surface-100">No emails scanned yet</p>
            <p class="text-muted mt-1">Click <strong class="text-surface-300">Scan Gmail</strong> to analyse your inbox with the ML model.</p>
          </div>
          <button id="btn-scan-empty" class="btn-primary" @click="startScan">Scan Gmail</button>
        </div>
      </div>

      <!-- Results -->
      <template v-else-if="!scanning && results.length > 0">
        <!-- Stats strip -->
        <ScanStats
          v-if="scanSummary"
          :summary="scanSummary"
          :active-filter="activeFilter"
          class="mb-6 animate-slide-up"
          @filter="(l) => (activeFilter = l)"
        />

        <!-- Controls row -->
        <div class="flex flex-col sm:flex-row gap-3 mb-4">
          <!-- Search -->
          <div class="relative flex-1">
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500 pointer-events-none" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35m0 0A7 7 0 104 10a7 7 0 0012.65 6.65z"/>
            </svg>
            <input
              id="input-search"
              v-model="searchQuery"
              class="input pl-9"
              placeholder="Search sender or subject…"
              type="text"
            />
          </div>

          <!-- Filter select -->
          <select
            id="select-filter"
            v-model="activeFilter"
            class="input sm:w-44"
          >
            <option value="">All labels</option>
            <option v-for="l in LABEL_ORDER" :key="l" :value="l">{{ l }}</option>
          </select>

          <!-- Result count -->
          <p class="text-muted self-center shrink-0 text-sm">
            {{ filteredResults.length }} of {{ results.length }} emails
          </p>
        </div>

        <!-- Table -->
        <div class="card !p-0 overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-surface-800 text-left">
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider w-64">Sender</th>
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">Subject</th>
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider w-48 hidden sm:table-cell">Label</th>
                <th class="px-4 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider w-24 text-right hidden md:table-cell">Confidence</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(email, index) in paginatedResults"
                :key="email.msg_id"
                class="border-b border-surface-800 last:border-0 hover:bg-surface-800/50 cursor-pointer transition-all duration-200 hover:-translate-y-[1px] animate-fade-in"
                @click="selectedEmail = email"
              >
                <td class="px-4 py-3 text-surface-300 truncate max-w-0 w-64">
                  <p class="truncate font-medium text-surface-200">{{ email.sender }}</p>
                </td>
                <td class="px-4 py-3 text-surface-400 truncate">
                  {{ email.subject || '(no subject)' }}
                </td>
                <td class="px-4 py-3 whitespace-nowrap hidden sm:table-cell">
                  <LabelBadge :label="email.primary_label" />
                </td>
                <td class="px-4 py-3 text-right text-surface-500 hidden md:table-cell tabular-nums">
                  {{ email.confidence > 0 ? `${Math.round(email.confidence * 100)}%` : '—' }}
                </td>
              </tr>
              <tr v-if="!filteredResults.length">
                <td colspan="4" class="px-4 py-8 text-center text-muted">No emails match your filter.</td>
              </tr>
            </tbody>
          </table>

          <!-- Pagination -->
          <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-surface-800">
            <button id="btn-prev-page" class="btn-ghost text-xs" :disabled="page === 1" @click="page--">← Previous</button>
            <p class="text-muted text-xs">Page {{ page }} of {{ totalPages }}</p>
            <button id="btn-next-page" class="btn-ghost text-xs" :disabled="page === totalPages" @click="page++">Next →</button>
          </div>
        </div>
      </template>
    </main>

    
<EmailDetails :email="selectedEmail" @close="selectedEmail = null" />
      </div>
    </main>
  </WavyBackground>
</template>

<script setup lang="ts">
import type { ScanResult } from '~/composables/useApi'
import { useMotionPresets } from '~/composables/useMotionPresets'

definePageMeta({ layout: false })

const { login, checkAuth, authenticated, logout, userPicture } = useAuth()
const { fadeUp, scaleIn, hoverLift } = useMotionPresets()
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref<string | null>(null)

const api = useApi()

function scrollToDashboard() {
  document.getElementById('dashboard')?.scrollIntoView({ behavior: 'smooth' })
}

function handleHeroAction() {
  scrollToDashboard()
  if (!scanning.value && results.value.length === 0 && !scanError.value) {
    // Small timeout to allow smooth scroll to begin
    setTimeout(() => {
      startScan()
    }, 500)
  }
}

// Try It section state
const tryItText = ref('')
const tryItLoading = ref(false)
const tryItResult = ref<{ label: string; confidence: number } | null>(null)
const tryItError = ref<string | null>(null)

async function handleTryIt() {
  if (!tryItText.value.trim()) return
  tryItLoading.value = true
  tryItError.value = null
  tryItResult.value = null
  
  try {
    const result = await api.predictMessage(tryItText.value)
    tryItResult.value = result
  } catch (err: any) {
    tryItError.value = err.message || 'Failed to analyze message'
  } finally {
    tryItLoading.value = false
  }
}

function clearTryIt() {
  tryItText.value = ''
  tryItResult.value = null
  tryItError.value = null
}

// === Dashboard State ===
const scanning = ref(false)
const stopping = ref(false)
const scanError = ref<string | null>(null)
const currentScanId = ref<string | null>(null)
const eventSource = ref<EventSource | null>(null)

// SSE Stream data
const scanLogs = ref<string[]>([])
const scanProgress = ref({ current: 0, total: 0 })
const results = ref<ScanResult[]>([])
const scanSummary = ref<Record<string, number> | null>(null)

// UI
const terminalEl = ref<HTMLElement | null>(null)
const selectedEmail = ref<ScanResult | null>(null)
const searchQuery = ref('')
const activeFilter = ref('')
const page = ref(1)
const PAGE_SIZE = 25

const LABEL_ORDER = [
  'Phishing', 'Spam', 'Security', 'Needs Review', 'Banking', 'Orders',
  'Work', 'Education', 'Promotions', 'Personal', 'Trusted',
]

// Auto-scroll terminal
watch(scanLogs, () => {
  nextTick(() => {
    if (terminalEl.value) {
      terminalEl.value.scrollTop = terminalEl.value.scrollHeight
    }
  })
}, { deep: true })

// Filtering & pagination
const filteredResults = computed(() => {
  let list = results.value
  if (activeFilter.value) {
    list = list.filter((r) => r.primary_label === activeFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(
      (r) =>
        r.sender.toLowerCase().includes(q) ||
        r.subject.toLowerCase().includes(q),
    )
  }
  return list
})

// Reset to first page whenever filter/search changes
watch([filteredResults], () => { page.value = 1 })

const totalPages = computed(() => Math.max(1, Math.ceil(filteredResults.value.length / PAGE_SIZE)))

const paginatedResults = computed(() =>
  filteredResults.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE),
)

function updateSummary() {
  const summary: Record<string, number> = {}
  for (const r of results.value) {
    const label = r.primary_label || 'Unknown'
    summary[label] = (summary[label] || 0) + 1
  }
  scanSummary.value = summary
}

// Scan lifecycle
let batchTimer: any = null
const resultBatchQueue: ScanResult[] = []

function startScan() {
  // Reset state
  scanning.value = true
  stopping.value = false
  scanError.value = null
  selectedEmail.value = null
  results.value = []
  scanSummary.value = null
  scanLogs.value = ['Connecting to Gmail...']
  scanProgress.value = { current: 0, total: 0 }
  
  currentScanId.value = crypto.randomUUID()
  const es = api.createScanStream(currentScanId.value)
  eventSource.value = es
  
  // Batch processing function to prevent mass animations
  const flushBatch = () => {
    if (resultBatchQueue.length > 0) {
      results.value.push(...resultBatchQueue)
      resultBatchQueue.length = 0
    }
  }

  // Set up 100ms batch timer for smooth stagger
  batchTimer = setInterval(flushBatch, 100)
  
  es.addEventListener('log', (e) => {
    const data = JSON.parse(e.data)
    scanLogs.value.push(data.message)
    if (scanLogs.value.length > 100) scanLogs.value.shift()
  })
  
  es.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data)
    scanProgress.value = data
  })
  
  es.addEventListener('start', (e) => {
    const data = JSON.parse(e.data)
    scanProgress.value.total = data.total
  })
  
  es.addEventListener('result', (e) => {
    const data = JSON.parse(e.data)
    resultBatchQueue.push(data)
  })
  
  es.addEventListener('done', (e) => {
    const data = JSON.parse(e.data)
    if (data.status === 'cancelled') scanError.value = 'Scan was cancelled.'
    flushBatch() // Flush final items
    clearInterval(batchTimer)
    closeStream()
    updateSummary()
  })
  
  es.addEventListener('error', (e) => {
    const data = JSON.parse(e.data)
    scanError.value = data.message || 'Unknown stream error.'
    flushBatch()
    clearInterval(batchTimer)
    closeStream()
    updateSummary()
  })
  
  es.onerror = (e) => {
    console.error('SSE Error:', e)
    if (!stopping.value) scanError.value = 'Connection to server lost.'
    flushBatch()
    clearInterval(batchTimer)
    closeStream()
    updateSummary()
  }
}

function closeStream() {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
  scanning.value = false
  stopping.value = false
  currentScanId.value = null
}

async function handleStopScan() {
  if (!currentScanId.value) return
  stopping.value = true
  scanLogs.value.push('Sending stop signal to server...')
  
  try {
    await api.stopScan(currentScanId.value)
  } catch (err: unknown) {
    scanLogs.value.push('Error stopping scan: ' + (err as Error).message)
    stopping.value = false
  }
}

async function handleLogout() {
  await logout()
}

// === Auth and Lifecycle ===
onMounted(async () => {
  await checkAuth()
  
  const code = route.query.code as string | undefined
  if (code) {
    loading.value = true
    error.value = null
    try {
      await api.submitCallback(code)
      await router.replace('/')
      await checkAuth()
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Authentication failed. Please try again.'
      loading.value = false
    }
  }
})

async function handleSignIn() {
  loading.value = true
  error.value = null
  try {
    await login()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Failed to start sign-in. Is the API server running?'
    loading.value = false
  }
}

onUnmounted(() => {
  if (eventSource.value) eventSource.value.close()
  if (batchTimer) clearInterval(batchTimer)
})
</script>


<style scoped>
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}
.animate-shimmer {
  transform: translateX(-100%);
  animation: shimmer 2s infinite;
}
</style>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
