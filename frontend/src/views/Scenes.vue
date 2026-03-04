<template>
  <div class="scenes-page">
    <el-container>
      <el-header>
        <h1>🎭 情景模拟 - Scenario Practice</h1>
      </el-header>
      
      <el-main>
        <!-- 分类筛选 -->
        <el-tabs v-model="activeCategory" @tab-change="filterScenes">
          <el-tab-pane label="全部" name="all" />
          <el-tab-pane label="💼 工作场景" name="work" />
          <el-tab-pane label="📚 学习场景" name="study" />
        </el-tabs>
        
        <!-- 场景列表 -->
        <el-row :gutter="20">
          <el-col 
            v-for="scene in filteredScenes" 
            :key="scene.id"
            :xs="24" 
            :sm="12" 
            :md="8"
          >
            <el-card 
              class="scene-card"
              :class="{ 'difficulty-hard': scene.difficulty === 'hard', 
                        'difficulty-medium': scene.difficulty === 'medium',
                        'difficulty-easy': scene.difficulty === 'easy' }"
              @click="showSceneDetail(scene)"
            >
              <template #header>
                <div class="scene-card-header">
                  <h3>{{ scene.name }}</h3>
                  <span class="difficulty-tag">{{ getDifficultyLabel(scene.difficulty) }}</span>
                </div>
              </template>
              
              <div class="scene-content">
                <p class="scene-name-en">{{ scene.nameEn }}</p>
                <p class="scene-description">{{ scene.description }}</p>
                
                <div class="scene-meta">
                  <el-tag size="small" v-for="tag in scene.tags.slice(0, 3)" :key="tag">
                    {{ tag }}
                  </el-tag>
                </div>
                
                <div class="scene-footer">
                  <span>⏱️ {{ scene.estimatedDuration }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 空状态 -->
        <el-empty v-if="filteredScenes.length === 0" description="暂无场景" />
      </el-main>
    </el-container>
    
    <!-- 场景详情对话框 -->
    <el-dialog 
      v-model="detailVisible" 
      title="场景详情"
      width="800px"
    >
      <div v-if="currentScene" class="scene-detail">
        <h2>{{ currentScene.name }} - {{ currentScene.nameEn }}</h2>
        
        <!-- 场景背景 -->
        <el-divider content-position="left">📖 场景背景</el-divider>
        <p class="background-text">{{ currentScene.background }}</p>
        
        <!-- 角色信息 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>🤖 AI 角色</span>
              </template>
              <div class="role-info">
                <h4>{{ currentScene.aiRole.name }}</h4>
                <p>{{ currentScene.aiRole.description }}</p>
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span>👤 你的角色</span>
              </template>
              <div class="role-info">
                <h4>{{ currentScene.userRole.name }}</h4>
                <p>{{ currentScene.userRole.description }}</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 建议话题 -->
        <el-divider content-position="left">💡 建议话题</el-divider>
        <div class="topics">
          <el-tag 
            v-for="topic in currentScene.suggestedTopics" 
            :key="topic"
            type="info"
            style="margin: 5px;"
          >
            {{ topic }}
          </el-tag>
        </div>
        
        <!-- 常用表达 -->
        <el-divider content-position="left">📝 常用表达</el-divider>
        <ul class="expressions">
          <li v-for="expr in currentScene.usefulExpressions" :key="expr">
            {{ expr }}
          </li>
        </ul>
      </div>
      
      <template #footer>
        <el-button @click="detailVisible = false">取消</el-button>
        <el-button type="primary" @click="startScene">开始练习</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'ScenesPage',
  setup() {
    const router = useRouter()
    const activeCategory = ref('all')
    const allScenes = ref([])
    const detailVisible = ref(false)
    const currentScene = ref(null)
    
    const API_BASE = 'http://127.0.0.1:8000/api/scenes'
    
    // 加载场景列表
    const loadScenes = async () => {
      try {
        const response = await axios.get(API_BASE + '/')
        allScenes.value = response.data.scenes || []
      } catch (error) {
        console.error('加载场景失败:', error)
      }
    }
    
    // 筛选场景
    const filteredScenes = computed(() => {
      if (activeCategory.value === 'all') {
        return allScenes.value
      }
      return allScenes.value.filter(s => s.category === activeCategory.value)
    })
    
    const filterScenes = () => {
      // computed handles it, this is just for the @tab-change event
    }
    
    // 显示详情
    const showSceneDetail = async (scene) => {
      try {
        const response = await axios.get(`${API_BASE}/${scene.id}`)
        currentScene.value = response.data
        detailVisible.value = true
      } catch (error) {
        console.error('加载场景详情失败:', error)
      }
    }
    
    // 开始场景
    const startScene = () => {
      if (!currentScene.value) return
      
      // 跳转到对话页面，带上场景 ID
      router.push({
        path: '/chat',
        query: {
          scene: currentScene.value.id,
          mode: 'scene'
        }
      })
    }
    
    // 难度标签
    const getDifficultyLabel = (diff) => {
      const labels = {
        easy: '简单',
        medium: '中等',
        hard: '困难'
      }
      return labels[diff] || diff
    }
    
    onMounted(() => {
      loadScenes()
    })
    
    return {
      activeCategory,
      allScenes,
      filteredScenes,
      detailVisible,
      currentScene,
      showSceneDetail,
      startScene,
      getDifficultyLabel,
      filterScenes
    }
  }
}
</script>

<style scoped>
.scenes-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.el-header {
  background-color: #409EFF;
  color: white;
  text-align: center;
  line-height: 60px;
}

.el-main {
  padding: 20px;
}

.scene-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.scene-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.scene-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.difficulty-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

.difficulty-easy .difficulty-tag {
  background-color: #67c23a;
  color: white;
}

.difficulty-medium .difficulty-tag {
  background-color: #e6a23c;
  color: white;
}

.difficulty-hard .difficulty-tag {
  background-color: #f56c6c;
  color: white;
}

.scene-name-en {
  color: #909399;
  font-size: 14px;
  margin-bottom: 10px;
}

.scene-description {
  color: #606266;
  font-size: 13px;
  margin-bottom: 15px;
  line-height: 1.5;
}

.scene-meta {
  margin-bottom: 10px;
}

.scene-footer {
  color: #909399;
  font-size: 12px;
}

.scene-detail {
  padding: 10px;
}

.background-text {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  line-height: 1.8;
}

.role-info h4 {
  margin: 0 0 10px 0;
  color: #409EFF;
}

.role-info p {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.topics {
  padding: 10px;
}

.expressions {
  padding-left: 20px;
  line-height: 2;
}

.expressions li {
  color: #606266;
}
</style>