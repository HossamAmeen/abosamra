<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { toTypedSchema } from '@vee-validate/zod'
import { useFieldArray, useForm } from 'vee-validate'
import { z } from 'zod'
import { Plus, Tag, Trash2 } from 'lucide-vue-next'
import { apiError } from '@/api/client'
import {
  createAdminOffer,
  listAdminOffers,
  setOfferActive,
  updateAdminOffer,
} from '@/api/admin/offers'
import { listAdminProducts } from '@/api/admin/products'
import AdminHeader from '@/components/admin/AdminHeader.vue'
import Button from '@/components/ui/Button.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Input from '@/components/ui/Input.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import { useToast } from '@/composables/useToast'
import { useCatalogStore } from '@/stores/catalog'
import type { AdminOffer, AdminOfferInput, AdminProduct, OfferType } from '@/types/api'
import { formatWeekdayDate } from '@/utils/date'
import { formatMoney } from '@/utils/money'

const TYPE_LABELS: Record<OfferType, string> = {
  percentage: 'خصم %',
  bundle: 'باكدج',
  free_delivery: 'توصيل مجاني',
}
const NAME_PLACEHOLDER: Record<OfferType, string> = {
  percentage: 'مثلاً: خصم البهارات',
  bundle: 'مثلاً: باكدج رمضان',
  free_delivery: 'مثلاً: توصيل مجاني للطلبات الكبيرة',
}

const toast = useToast()
const catalog = useCatalogStore()
catalog.loadCategories()

const offers = ref<AdminOffer[]>([])
const loading = ref(true)
const failed = ref(false)
const products = ref<AdminProduct[]>([])
const editing = ref<AdminOffer | null>(null)
const formError = ref('')

const localDate = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

const positive = (msg: string) => z.string().refine((v) => v.trim() !== '' && Number(v) > 0, msg)

const schema = toTypedSchema(
  z
    .object({
      type: z.enum(['percentage', 'bundle', 'free_delivery']),
      name: z.string().trim().min(1, 'اكتب اسم العرض'),
      value: z.string(),
      target_kind: z.enum(['category', 'products', 'all']),
      target_slug: z.string(),
      target_ids: z.array(z.number()),
      bundle_items: z.array(z.object({ variant_id: z.string(), qty: z.string() })),
      bundle_price: z.string(),
      min_order: z.string(),
      starts: z.string().min(1, 'اختار تاريخ البداية'),
      ends: z.string(),
      is_featured: z.boolean(),
    })
    .superRefine((v, ctx) => {
      const add = (path: string, message: string) =>
        ctx.addIssue({ code: 'custom', path: path.split('.'), message })
      if (v.type === 'percentage') {
        const n = Number(v.value)
        if (v.value.trim() === '' || !(n >= 1 && n <= 90)) add('value', 'نسبة الخصم من 1 لـ 90')
        if (v.target_kind === 'category' && !v.target_slug) add('target_slug', 'اختار القسم')
        if (v.target_kind === 'products' && !v.target_ids.length)
          add('target_ids', 'اختار منتج واحد على الأقل')
      }
      if (v.type === 'bundle') {
        if (v.bundle_items.length < 2) add('bundle_items', 'الباكدج لازم فيه منتجين على الأقل')
        v.bundle_items.forEach((b, i) => {
          if (!b.variant_id) add(`bundle_items.${i}.variant_id`, 'اختار المنتج')
          if (!(Number(b.qty) >= 1)) add(`bundle_items.${i}.qty`, 'الكمية 1 أو أكتر')
        })
        if (!positive('x').safeParse(v.bundle_price).success)
          add('bundle_price', 'اكتب سعر الباكدج')
      }
      if (v.type === 'free_delivery' && !positive('x').safeParse(v.min_order).success) {
        add('min_order', 'اكتب أقل قيمة للطلب')
      }
      if (v.ends && v.starts && v.ends < v.starts) add('ends', 'تاريخ الانتهاء قبل البداية')
    }),
)

function emptyValues() {
  return {
    type: 'percentage' as OfferType,
    name: '',
    value: '',
    target_kind: 'category' as 'category' | 'products' | 'all',
    target_slug: '',
    target_ids: [] as number[],
    bundle_items: [] as { variant_id: string; qty: string }[],
    bundle_price: '',
    min_order: '',
    starts: localDate(new Date()),
    ends: '',
    is_featured: false,
  }
}

const {
  errors: rawErrors,
  values,
  defineField,
  handleSubmit,
  resetForm,
  setValues,
  setErrors,
  isSubmitting,
  submitCount,
} = useForm({ validationSchema: schema, initialValues: emptyValues() })
// Pristine form shows no errors; they appear only once the user pressed "نشر العرض".
const errors = computed<Record<string, string | undefined>>(() =>
  submitCount.value > 0 ? rawErrors.value : {},
)
const [name] = defineField('name')
const [value] = defineField('value')
const [bundlePrice] = defineField('bundle_price')
const [minOrder] = defineField('min_order')
const [starts] = defineField('starts')
const [ends] = defineField('ends')
const {
  fields: bundleRows,
  push: addBundleRow,
  remove: removeBundleRow,
} = useFieldArray<{ variant_id: string; qty: string }>('bundle_items')

const err = (key: string) => (errors.value as Record<string, string | undefined>)[key]

const variantOptions = computed(() =>
  products.value.flatMap((p) =>
    p.variants.map((v) => ({
      id: v.id,
      label: `${p.name} - ${v.label} (${formatMoney(v.price)})`,
    })),
  ),
)

function setType(t: OfferType) {
  setValues({ type: t })
  setErrors({})
}

function toggleProduct(id: number, on: boolean) {
  const ids = new Set(values.target_ids ?? [])
  if (on) ids.add(id)
  else ids.delete(id)
  setValues({ target_ids: [...ids] })
}

function startEdit(o: AdminOffer) {
  editing.value = o
  formError.value = ''
  resetForm({
    values: {
      type: o.type,
      name: o.name,
      value: o.value == null ? '' : String(o.value),
      target_kind: o.target?.kind ?? 'category',
      target_slug: o.target?.slug ?? '',
      target_ids: o.target?.ids ?? [],
      bundle_items: o.bundle_items.map((b) => ({
        variant_id: String(b.variant_id),
        qty: String(b.qty),
      })),
      bundle_price: o.bundle_price == null ? '' : String(o.bundle_price),
      min_order: o.min_order == null ? '' : String(o.min_order),
      starts: localDate(new Date(o.starts_at)),
      ends: o.ends_at ? localDate(new Date(o.ends_at)) : '',
      is_featured: o.is_featured,
    },
  })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  editing.value = null
  formError.value = ''
  resetForm({ values: emptyValues() })
}

function buildInput(v: ReturnType<typeof emptyValues>): AdminOfferInput {
  const input: AdminOfferInput = {
    type: v.type,
    name: v.name.trim(),
    starts_at: new Date(`${v.starts}T00:00:00`).toISOString(),
    ends_at: v.ends ? new Date(`${v.ends}T23:59:59`).toISOString() : null,
    is_featured: v.is_featured,
  }
  if (v.type === 'percentage') {
    input.value = Number(v.value)
    input.target =
      v.target_kind === 'category'
        ? { kind: 'category', slug: v.target_slug, ids: [] }
        : v.target_kind === 'products'
          ? { kind: 'products', slug: null, ids: v.target_ids }
          : { kind: 'all', slug: null, ids: [] }
  } else if (v.type === 'bundle') {
    input.bundle_items = v.bundle_items.map((b) => ({
      variant_id: Number(b.variant_id),
      qty: Number(b.qty),
    }))
    input.bundle_price = Number(v.bundle_price)
  } else {
    input.min_order = Number(v.min_order)
  }
  return input
}

const submit = handleSubmit(async (v) => {
  formError.value = ''
  try {
    const input = buildInput(v)
    if (editing.value) {
      const saved = await updateAdminOffer(editing.value.id, input)
      offers.value = offers.value.map((o) => (o.id === saved.id ? saved : o))
      toast.show('تم تعديل العرض')
    } else {
      offers.value = [await createAdminOffer(input), ...offers.value]
      toast.show('تم نشر العرض')
    }
    cancelEdit()
  } catch (e) {
    const { status, body } = apiError(e)
    if (status === 400) {
      const out: Record<string, string> = {}
      for (const [k, val] of Object.entries(body)) {
        if (k !== 'detail' && k !== 'code') out[k] = [val].flat().join(' ')
      }
      const map: Record<string, string> = { target: 'target_slug', bundle_items: 'bundle_items' }
      const mapped = Object.fromEntries(Object.entries(out).map(([k, m]) => [map[k] ?? k, m]))
      setErrors(mapped)
      if (!Object.keys(mapped).length) formError.value = body.detail ?? 'بيانات العرض مش صحيحة'
    } else {
      formError.value = body.detail ?? 'مقدرناش ننشر العرض، جرّب تاني'
    }
  }
})

async function toggle(o: AdminOffer, on: boolean) {
  const previous = o.is_active
  o.is_active = on
  try {
    await setOfferActive(o.id, on)
  } catch {
    o.is_active = previous
    toast.show('معرفناش نغيّر حالة العرض، جرّب تاني', { duration: 4000 })
  }
}

const targetChoice = computed(() =>
  values.target_kind === 'category'
    ? values.target_slug
      ? `cat:${values.target_slug}`
      : ''
    : (values.target_kind ?? ''),
)
function pickTarget(v: string) {
  if (v.startsWith('cat:')) setValues({ target_kind: 'category', target_slug: v.slice(4) })
  else setValues({ target_kind: v as 'products' | 'all', target_slug: '' })
}

/** Card headline as in the design: `15% على كل البهارات`, `باكدج الشتا · 290 ج.م`. */
const allOf = (n: string) => (n.includes(' ') ? `كل ${n}` : `كل ال${n}`)
function headline(o: AdminOffer) {
  if (o.type === 'percentage') {
    const t = o.target
    const where =
      t?.kind === 'category'
        ? allOf(catalog.categories.find((c) => c.slug === t.slug)?.name ?? '')
        : t?.kind === 'products'
          ? 'منتجات معينة'
          : 'كل المتجر'
    return `${o.value}% على ${where}`
  }
  if (o.type === 'bundle') return `${o.name} · ${formatMoney(o.bundle_price ?? 0)}`
  return `توصيل مجاني فوق ${formatMoney(o.min_order ?? 0)}`
}

/** The owner's name is a second line only when it and the derived headline do not already contain each other. */
function showName(o: AdminOffer) {
  if (o.type === 'bundle' || !o.name) return false
  const name = o.name.trim()
  const h = headline(o)
  return !h.includes(name) && !name.includes(h)
}

function validity(o: AdminOffer) {
  return o.ends_at ? `لحد ${formatWeekdayDate(o.ends_at)}` : 'من غير تاريخ انتهاء'
}
async function load() {
  loading.value = true
  failed.value = false
  try {
    offers.value = await listAdminOffers()
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

async function loadProducts() {
  try {
    let page = 1
    const all: AdminProduct[] = []
    for (;;) {
      const res = await listAdminProducts({ page })
      all.push(...res.results)
      if (!res.next || page >= 10) break
      page += 1
    }
    products.value = all
  } catch {
    /* pickers stay empty; the form reports missing items on submit */
  }
}

onMounted(() => {
  void load()
  void loadProducts()
})

const selectClass =
  'h-[50px] w-full rounded-field border bg-white px-[14px] text-[15px] text-ink border-input-border'
</script>

<template>
  <div>
    <AdminHeader title="العروض" />

    <div class="flex flex-col gap-5 p-4">
      <form
        class="flex flex-col gap-4 rounded-card border border-border bg-surface p-4"
        novalidate
        aria-label="عرض جديد"
        @submit.prevent="submit"
      >
        <h2 class="text-[17px] font-extrabold text-ink">
          {{ editing ? 'تعديل العرض' : 'عرض جديد' }}
        </h2>

        <div
          role="radiogroup"
          aria-label="نوع العرض"
          class="flex gap-1 rounded-btn bg-primary-tint p-1"
        >
          <button
            v-for="(label, t) in TYPE_LABELS"
            :key="t"
            type="button"
            role="radio"
            :aria-checked="values.type === t"
            :disabled="!!editing"
            :class="[
              'min-h-[44px] flex-1 rounded-field text-[14px] font-bold',
              values.type === t ? 'bg-primary text-ink' : 'text-brand-deep',
            ]"
            @click="setType(t as OfferType)"
          >
            {{ label }}
          </button>
        </div>

        <Input
          v-model="name"
          label="اسم العرض"
          :placeholder="NAME_PLACEHOLDER[values.type ?? 'percentage']"
          :error="errors.name"
        />

        <template v-if="values.type === 'percentage'">
          <div class="grid grid-cols-2 gap-3">
            <Input
              v-model="value"
              label="نسبة الخصم %"
              type="number"
              inputmode="numeric"
              ltr
              :error="errors.value"
            />
            <div class="flex flex-col gap-1.5">
              <label for="target" class="text-[14px] font-bold text-ink">على</label>
              <select
                id="target"
                :value="targetChoice"
                :class="[selectClass, errors.target_slug ? '!border-danger' : '']"
                @change="pickTarget(($event.target as HTMLSelectElement).value)"
              >
                <option value="" disabled>اختار</option>
                <option v-for="c in catalog.categories" :key="c.slug" :value="`cat:${c.slug}`">
                  قسم {{ c.name }}
                </option>
                <option value="products">منتجات معينة</option>
                <option value="all">كل المتجر</option>
              </select>
              <p
                v-if="errors.target_slug"
                class="text-[13px] font-semibold text-danger"
                role="alert"
              >
                {{ errors.target_slug }}
              </p>
            </div>
          </div>
          <fieldset v-if="values.target_kind === 'products'" class="flex flex-col gap-1">
            <legend class="mb-1 text-[14px] font-bold text-ink">المنتجات</legend>
            <div class="max-h-52 overflow-y-auto rounded-field border border-input-border">
              <label
                v-for="p in products"
                :key="p.id"
                class="flex min-h-[44px] items-center gap-3 px-3 text-[14px]"
              >
                <input
                  type="checkbox"
                  class="h-5 w-5"
                  :checked="values.target_ids?.includes(p.id)"
                  @change="toggleProduct(p.id, ($event.target as HTMLInputElement).checked)"
                />
                {{ p.name }}
              </label>
            </div>
            <p v-if="errors.target_ids" class="text-[13px] font-semibold text-danger" role="alert">
              {{ errors.target_ids }}
            </p>
          </fieldset>
        </template>

        <template v-else-if="values.type === 'bundle'">
          <fieldset class="flex flex-col gap-2">
            <legend class="mb-1 text-[14px] font-bold text-ink">المنتجات اللي في الباكدج</legend>
            <div
              v-for="(row, i) in bundleRows"
              :key="row.key"
              class="grid grid-cols-[1fr_72px_44px] items-start gap-2"
            >
              <div class="flex flex-col gap-1">
                <select
                  v-model="row.value.variant_id"
                  :class="selectClass"
                  :aria-label="`المنتج ${i + 1}`"
                >
                  <option value="" disabled>اختار المنتج</option>
                  <option v-for="o in variantOptions" :key="o.id" :value="String(o.id)">
                    {{ o.label }}
                  </option>
                </select>
                <p
                  v-if="err(`bundle_items[${i}].variant_id`)"
                  class="text-[13px] font-semibold text-danger"
                  role="alert"
                >
                  {{ err(`bundle_items[${i}].variant_id`) }}
                </p>
              </div>
              <Input
                v-model="row.value.qty"
                type="number"
                inputmode="numeric"
                ltr
                :aria-label="`كمية المنتج ${i + 1}`"
                :error="err(`bundle_items[${i}].qty`)"
              />
              <button
                type="button"
                :aria-label="`حذف المنتج ${i + 1} من الباكدج`"
                class="flex h-[50px] w-11 items-center justify-center rounded-field bg-[#FDE7E5] text-danger"
                @click="removeBundleRow(i)"
              >
                <Trash2 class="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <p
              v-if="errors.bundle_items"
              class="text-[13px] font-semibold text-danger"
              role="alert"
            >
              {{ errors.bundle_items }}
            </p>
            <button
              type="button"
              class="flex h-11 items-center justify-center gap-2 rounded-field border-2 border-dashed border-[#E3B98E] font-bold text-brand-deep"
              @click="addBundleRow({ variant_id: '', qty: '1' })"
            >
              <Plus class="h-5 w-5" aria-hidden="true" />
              إضافة منتج
            </button>
          </fieldset>
          <Input
            v-model="bundlePrice"
            label="سعر الباكدج (ج.م)"
            type="number"
            inputmode="decimal"
            ltr
            :error="errors.bundle_price"
          />
        </template>

        <Input
          v-else
          v-model="minOrder"
          label="أقل قيمة للطلب (ج.م)"
          type="number"
          inputmode="decimal"
          ltr
          :error="errors.min_order"
        />

        <div class="grid grid-cols-2 gap-3">
          <Input v-model="starts" label="يبدأ من" type="date" ltr :error="errors.starts" />
          <Input v-model="ends" label="ينتهي في" optional type="date" ltr :error="errors.ends" />
        </div>

        <label class="flex min-h-[44px] items-center gap-3 text-[14px] font-bold text-ink">
          <input
            type="checkbox"
            class="h-5 w-5"
            :checked="values.is_featured"
            @change="setValues({ is_featured: ($event.target as HTMLInputElement).checked })"
          />
          يظهر كعرض الأسبوع في الرئيسية
        </label>

        <p v-if="formError" class="text-[14px] font-bold text-danger" role="alert">
          {{ formError }}
        </p>

        <Button type="submit" block :loading="isSubmitting">
          {{ editing ? 'حفظ التعديلات' : 'نشر العرض' }}
        </Button>
        <Button v-if="editing" variant="secondary" block @click="cancelEdit">إلغاء التعديل</Button>
      </form>

      <section class="flex flex-col gap-3">
        <h2 class="text-[17px] font-extrabold text-ink">العروض الحالية</h2>
        <template v-if="loading">
          <Skeleton v-for="i in 3" :key="i" class="h-[80px]" />
        </template>
        <p v-else-if="failed" class="text-[14px] font-bold text-danger" role="alert">
          مقدرناش نحمّل العروض
          <button type="button" class="min-h-[44px] ms-2 text-link underline" @click="load">
            حاول تاني
          </button>
        </p>
        <EmptyState v-else-if="!offers.length" :icon="Tag" text="مفيش عروض لسه" />
        <template v-else>
          <article
            v-for="o in offers"
            :key="o.id"
            class="flex items-center gap-3 rounded-card border border-border bg-surface p-3"
          >
            <button
              type="button"
              class="flex min-h-[44px] flex-1 flex-col gap-1 text-start"
              @click="startEdit(o)"
            >
              <span
                class="w-fit rounded-full bg-primary-soft px-3 py-0.5 text-[12px] font-bold text-brand-deep"
              >
                {{ TYPE_LABELS[o.type] }}
              </span>
              <span class="text-[15px] font-extrabold text-ink">{{ headline(o) }}</span>
              <span v-if="showName(o)" class="text-[12px] text-ink-2">{{ o.name }}</span>
              <span class="text-[12px] text-muted">{{ validity(o) }}</span>
            </button>
            <ToggleSwitch
              :model-value="o.is_active"
              label-on="شغّال"
              label-off="واقف"
              :aria-label="`${o.name}: شغّال`"
              @update:model-value="toggle(o, $event)"
            />
          </article>
        </template>
      </section>
    </div>
  </div>
</template>
