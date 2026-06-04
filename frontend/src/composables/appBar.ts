import {
  ref,
  shallowRef,
  readonly,
  onMounted,
  onUnmounted,
  computed,
} from 'vue'

interface AppBarAction {
  icon: string
  label: string
  action: () => void
}

const title = shallowRef('')
const actions = shallowRef<AppBarAction[]>([])
const activeJobs = ref<Set<string>>(new Set())
const isBusy = computed(() => activeJobs.value.size > 0)

export function useAppBar() {
  function setContext(newTitle: string, newActions: AppBarAction[] = []) {
    title.value = newTitle
    actions.value = newActions
  }

  function clearContext() {
    title.value = ''
    actions.value = []
  }

  function startJob(jobId: string) {
    activeJobs.value.add(jobId)
  }

  function endJob(jobId: string) {
    activeJobs.value.delete(jobId)
  }

  return {
    title: readonly(title),
    actions: readonly(actions),
    startJob,
    endJob,
    setContext,
    clearContext,
    isBusy,
  }
}

/**
 * Sets the app-bar context for the current component.
 * @param newTitle The app-bar title
 * @param newActions Actions for the app-bar
 */
export function useAppBarContext(
  newTitle: string,
  newActions: AppBarAction[] = [],
) {
  const { setContext, clearContext } = useAppBar()
  onMounted(() => setContext(newTitle, newActions))
  onUnmounted(() => clearContext())
}
