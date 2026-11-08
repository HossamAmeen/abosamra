<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toTypedSchema } from '@vee-validate/zod'
import { useFieldArray, useForm } from 'vee-validate'
import { z } from 'zod'
import { Image as ImageIcon, Plus, Trash2 } from 'lucide-vue-next'
import { apiError } from '@/api/client'
import {
  createAdminProduct,
  deleteAdminProduct,
  getAdminProduct,
  updateAdminProduct,
} from '@/api/admin/products'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import TopBar from '@/components/ui/TopBar.vue'
import { useToast } from '@/composables/useToast'
import { useCatalogStore } from '@/stores/catalog'
import type { AdminProduct, AdminProductInput } from '@/types/api'
import { compressImage } from '@/utils/image'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const catalog = useCatalogStore()
catalog.loadCategories()

const id = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => id.value !== null)

const optionalNumber = z
  .string()
  .trim()
  .refine((v) => v === '' || (!Number.isNaN(Number(v)) && Number(v) >= 0), 'اكتب رقم صحيح')

const schema = toTypedSchema(
  z.object({
    name: z.string().trim().min(2, 'اكتب اسم المنتج'),
    category: z.string().min(1, 'اختار القسم'),
    description: z.string(),
    is_available: z.boolean(),
    is_featured: z.boolean(),
    stock_qty: optionalNumber,
    low_stock_threshold: optionalNumber,
    stock_unit: z.string().trim(),
    variants: z
      .array(
        z.object({
          id: z.number().optional(),
          label: z.string().trim().min(1, 'اكتب الوزن'),
          price: z
            .string()
            .trim()
            .refine((v) => v !== '' && Number(v) > 0, 'اكتب سعر صحيح'),
        }),
      )
      .min(1, 'ضيف وزن واحد على الأقل'),
  }),
)

const {
  errors,
  values,
  defineField,
  handleSubmit,
  setValues,
  setErrors,
  isSubmitting,
  submitCount,
} = useForm({
  validationSchema: schema,
  initialValues: {
    name: '',
    category: '',
    description: '',
    is_available: true,
    is_featured: false,
    stock_qty: '',
    low_stock_threshold: '',
    stock_unit: '',
    variants: [
      { label: '', price: '' },
      { label: '', price: '' },
      { label: '', price: '' },
    ],
  },
})
const [name] = defineField('name')
const [category] = defineField('category')
const [description] = defineField('description')
const [stockQty] = defineField('stock_qty')
const [lowStock] = defineField('low_stock_threshold')
const [stockUnit] = defineField('stock_unit')
const { fields, push, remove } = useFieldArray<{ id?: number; label: string; price: string }>(
  'variants',
)

/** Row errors only after a submit attempt, so a fresh form isn't red. */
const rowError = (i: number, field: 'label' | 'price') =>
  submitCount.value > 0
    ? (errors.value as Record<string, string | undefined>)[`variants[${i}].${field}`]
    : undefined

const loading = ref(false)
const loadFailed = ref(false)
const imageFile = ref<File | null>(null)
const preview = ref<string | null>(null)
const formError = ref('')
const confirmDelete = ref(false)
const deleting = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const str = (v: unknown) => (v == null ? '' : String(Number(v)))

function fill(p: AdminProduct) {
  setValues({
    name: p.name,
    category: String(p.category.id),
    description: p.description,
    is_available: p.is_available,
    is_featured: p.is_featured,
    stock_qty: str(p.stock_qty),
    low_stock_threshold: str(p.low_stock_threshold),
    stock_unit: p.stock_unit,
    variants: p.variants.map((v) => ({ id: v.id, label: v.label, price: String(v.price) })),
  })
  preview.value = p.image
}

async function loadProduct() {
  if (!isEdit.value) return
  loading.value = true
  loadFailed.value = false
  try {
    fill(await getAdminProduct(id.value!))
  } catch {
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}
onMounted(loadProduct)
onBeforeUnmount(() => {
  if (preview.value?.startsWith('blob:')) URL.revokeObjectURL(preview.value)
})

async function onPickImage(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const compressed = await compressImage(file)
  imageFile.value = compressed
  if (preview.value?.startsWith('blob:')) URL.revokeObjectURL(preview.value)
  preview.value = URL.createObjectURL(compressed)
}

/** Map DRF `{field: [msg]}` (and nested variants errors) onto the form inputs. */
function mapServerErrors(body: Record<string, unknown>) {
  const out: Record<string, string> = {}
  for (const [key, val] of Object.entries(body)) {
    if (key === 'detail' || key === 'code') continue
    if (key === 'variants' && Array.isArray(val)) {
      val.forEach((item, i) => {
        if (typeof item === 'string') out.variants = item
        else if (item && typeof item === 'object') {
          for (const [f, msgs] of Object.entries(item as Record<string, unknown>)) {
            out[`variants[${i}].${f}`] = [msgs].flat().join(' ')
          }
        }
      })
    } else {
      out[key] = [val].flat().join(' ')
    }
  }
  setErrors(out)
  return Object.keys(out).length > 0
}

const toNumberOrNull = (v: string) => (v.trim() === '' ? null : Number(v))

const onSubmit = handleSubmit(async (v) => {
  formError.value = ''
  const payload: AdminProductInput = {
    name: v.name.trim(),
    category: Number(v.category),
    description: v.description,
    is_available: v.is_available,
    is_featured: v.is_featured,
    stock_qty: toNumberOrNull(v.stock_qty),
    low_stock_threshold: toNumberOrNull(v.low_stock_threshold),
    stock_unit: v.stock_unit.trim(),
    variants: v.variants.map((x, i) => ({
      ...(x.id ? { id: x.id } : {}),
      label: x.label.trim(),
      price: Number(x.price),
      is_default: i === 0,
      order: i,
    })),
    image: imageFile.value,
  }
  try {
    if (isEdit.value) await updateAdminProduct(id.value!, payload)
    else await createAdminProduct(payload)
    toast.show('تم حفظ المنتج')
    router.push('/admin/products')
  } catch (e) {
    const { status, body } = apiError(e)
    const mapped = status === 400 && mapServerErrors(body)
    if (!mapped) formError.value = body.detail ?? 'مقدرناش نحفظ المنتج، جرّب تاني'
  }
})

async function remove_() {
  deleting.value = true
  try {
    await deleteAdminProduct(id.value!)
    toast.show('تم حذف المنتج')
    router.push('/admin/products')
  } catch (e) {
    formError.value = apiError(e).body.detail ?? 'مقدرناش نحذف المنتج'
    confirmDelete.value = false
  } finally {
    deleting.value = false
  }
}

const selectClass =
  'h-[50px] w-full rounded-field border bg-white px-[14px] text-[15px] text-ink border-input-border'
</script>

<template>
  <div class="pb-28">
    <TopBar :title="isEdit ? 'تعديل منتج' : 'إضافة منتج'" back-to="/admin/products" />

    <div v-if="loading" class="flex flex-col gap-3 p-4">
      <Skeleton v-for="i in 4" :key="i" class="h-[60px]" />
    </div>
    <p v-else-if="loadFailed" class="p-4 text-[14px] font-bold text-danger" role="alert">
      مقدرناش نحمّل المنتج
      <button type="button" class="min-h-[44px] ms-2 text-link underline" @click="loadProduct">
        حاول تاني
      </button>
    </p>

    <form
      v-else
      id="product-form"
      class="flex flex-col gap-4 p-4"
      novalidate
      @submit.prevent="onSubmit"
    >
      <div>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          class="sr-only"
          aria-label="صورة المنتج"
          data-testid="image-input"
          @change="onPickImage"
        />
        <button
          type="button"
          class="flex h-[150px] w-full flex-col items-center justify-center gap-2 overflow-hidden rounded-card border-2 border-dashed border-[#E3B98E] bg-primary-tint text-brand-deep"
          @click="fileInput?.click()"
        >
          <img v-if="preview" :src="preview" alt="صورة المنتج" class="h-full w-full object-cover" />
          <template v-else>
            <ImageIcon class="h-9 w-9" aria-hidden="true" />
            <span class="text-[14px] font-bold">اضغط لإضافة صورة المنتج</span>
          </template>
        </button>
      </div>

      <Input
        v-model="name"
        label="اسم المنتج"
        placeholder="مثلاً: كمون مطحون"
        :error="errors.name"
      />

      <div class="flex flex-col gap-1.5">
        <label for="category" class="text-[14px] font-bold text-ink">القسم</label>
        <select
          id="category"
          v-model="category"
          :class="[selectClass, errors.category ? '!border-danger' : '']"
          :aria-invalid="!!errors.category || undefined"
        >
          <option value="" disabled>اختار القسم</option>
          <option v-for="c in catalog.categories" :key="c.id" :value="String(c.id)">
            {{ c.name }}
          </option>
        </select>
        <p v-if="errors.category" class="text-[13px] font-semibold text-danger" role="alert">
          {{ errors.category }}
        </p>
      </div>

      <fieldset class="flex flex-col gap-2">
        <legend class="mb-1 text-[14px] font-bold text-ink">الأسعار حسب الوزن</legend>
        <div class="grid grid-cols-[1fr_1fr_44px] gap-2 text-[13px] font-semibold text-ink-2">
          <span>الوزن</span><span>السعر (ج.م)</span><span />
        </div>
        <div
          v-for="(f, i) in fields"
          :key="f.key"
          class="grid grid-cols-[1fr_1fr_44px] items-start gap-2"
        >
          <Input
            v-model="f.value.label"
            aria-label="الوزن"
            :placeholder="['ربع كيلو', 'نص كيلو', 'كيلو'][i] ?? 'كيلو'"
            :error="rowError(i, 'label')"
          />
          <Input
            v-model="f.value.price"
            aria-label="السعر"
            type="number"
            inputmode="decimal"
            ltr
            :placeholder="['60', '115', '220'][i] ?? ''"
            :error="rowError(i, 'price')"
          />
          <button
            type="button"
            :aria-label="`حذف الوزن ${i + 1}`"
            class="flex h-[50px] w-11 items-center justify-center rounded-field bg-[#FDE7E5] text-danger disabled:opacity-40"
            :disabled="fields.length <= 1"
            @click="remove(i)"
          >
            <Trash2 class="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        <p
          v-if="errors.variants && submitCount > 0"
          class="text-[13px] font-semibold text-danger"
          role="alert"
        >
          {{ errors.variants }}
        </p>
        <button
          type="button"
          class="flex h-11 w-fit items-center justify-center gap-2 rounded-field border-2 border-dashed border-[#E3B98E] px-4 font-bold text-brand-deep"
          @click="push({ label: '', price: '' })"
        >
          <Plus class="h-5 w-5" aria-hidden="true" />
          إضافة وزن
        </button>
      </fieldset>

      <Input
        v-model="description"
        label="وصف قصير"
        multiline
        :rows="3"
        placeholder="اكتب سطرين عن المنتج واستخداماته"
        :error="errors.description"
      />

      <section
        class="flex flex-col divide-y divide-border rounded-card border border-border bg-surface px-4"
      >
        <div class="flex min-h-[56px] items-center justify-between">
          <span class="text-[15px] font-bold text-ink">متاح للبيع</span>
          <ToggleSwitch
            :model-value="values.is_available ?? true"
            label-on="نعم"
            label-off="لا"
            aria-label="متاح للبيع"
            @update:model-value="setValues({ is_available: $event })"
          />
        </div>
        <div class="flex min-h-[56px] items-center justify-between">
          <span class="text-[15px] font-bold text-ink">يظهر في "الأكثر طلباً"</span>
          <ToggleSwitch
            :model-value="values.is_featured ?? false"
            label-on="نعم"
            label-off="لا"
            aria-label="يظهر في الأكثر طلباً"
            @update:model-value="setValues({ is_featured: $event })"
          />
        </div>
      </section>

      <section class="grid grid-cols-3 gap-2">
        <Input
          v-model="stockQty"
          label="الكمية"
          optional
          type="number"
          inputmode="decimal"
          ltr
          :error="errors.stock_qty"
        />
        <Input
          v-model="lowStock"
          label="حد التنبيه"
          optional
          type="number"
          inputmode="decimal"
          ltr
          :error="errors.low_stock_threshold"
        />
        <Input
          v-model="stockUnit"
          label="الوحدة"
          optional
          placeholder="كيلو"
          :error="errors.stock_unit"
        />
      </section>

      <p v-if="formError" class="text-[14px] font-bold text-danger" role="alert">{{ formError }}</p>

      <Button v-if="isEdit" variant="danger-text" @click="confirmDelete = true">حذف المنتج</Button>
    </form>

    <div
      class="pb-safe fixed inset-x-0 bottom-0 z-40 mx-auto flex max-w-admin gap-2 border-t border-border bg-surface p-3"
    >
      <Button
        type="submit"
        form="product-form"
        class="flex-[2]"
        :loading="isSubmitting"
        :disabled="loading || loadFailed"
      >
        حفظ المنتج
      </Button>
      <Button variant="secondary" class="flex-1" @click="router.push('/admin/products')"
        >إلغاء</Button
      >
    </div>

    <BottomSheet v-if="confirmDelete" title="حذف المنتج" @close="confirmDelete = false">
      <p class="mb-3 text-[15px] font-bold text-ink">
        متأكد إنك عايز تحذف المنتج ده؟ لو عليه طلبات قديمة هيتخبّى بدل ما يتمسح.
      </p>
      <div class="grid grid-cols-2 gap-2">
        <Button variant="danger" :loading="deleting" @click="remove_">أيوه، احذف</Button>
        <Button variant="secondary" @click="confirmDelete = false">لأ</Button>
      </div>
    </BottomSheet>
  </div>
</template>
