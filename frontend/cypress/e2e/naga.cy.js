describe('NAGA E2E Tests', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('successfully loads the scenes page', () => {
    cy.contains('h1', '情景模拟 - Scenario Practice').should('be.visible')
  })

  it('can open a scene dialog and start practice', () => {
    // 假设场景列表已经加载
    cy.contains('.scene-card', '面试自我介绍').click()
    
    // 验证弹窗出现
    cy.get('.el-dialog').should('be.visible')
    cy.contains('.el-dialog h2', '面试自我介绍 - Self Introduction').should('be.visible')
    
    // 点击开始练习
    cy.contains('button', '开始练习').click()
    
    // 验证跳转到对话页面
    cy.url().should('include', '/chat?scene=interview_001')
    cy.contains('h1', '情景练习: 面试自我介绍').should('be.visible')
  })

  it('can send a message in chat', () => {
    cy.visit('/chat')
    cy.contains('h1', '自由练习').should('be.visible')
    
    // 输入消息
    cy.get('input[placeholder*="输入文字"]').type('Hello there{enter}')
    
    // 验证消息出现在列表中
    cy.get('.message.user .text').last().should('contain', 'Hello there')
  })
})