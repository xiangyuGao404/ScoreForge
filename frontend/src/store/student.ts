import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Student {
  id: string
  name: string
  grade: string
  school: string
  subjects: string[]
}

export const useStudentStore = defineStore('student', () => {
  const students = ref<Student[]>([])
  const currentStudentId = ref(uni.getStorageSync('currentStudentId') || '')

  const currentStudent = computed(() =>
    students.value.find(s => s.id === currentStudentId.value) || students.value[0]
  )

  function setStudents(list: Student[]) {
    students.value = list
    if (!currentStudentId.value && list.length > 0) {
      switchStudent(list[0].id)
    }
  }

  function switchStudent(id: string) {
    currentStudentId.value = id
    uni.setStorageSync('currentStudentId', id)
  }

  const subjectLabel: Record<string, string> = {
    math: '数学',
    politics: '道法',
    history: '历史',
  }

  function getSubjectName(key: string) {
    return subjectLabel[key] || key
  }

  return { students, currentStudentId, currentStudent, setStudents, switchStudent, getSubjectName }
})
