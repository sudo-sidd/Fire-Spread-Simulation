#!/usr/bin/env python3
"""
Simple test to check if OpenGL/graphics work at all
"""

import pygame
import sys

def test_pygame():
    """Test basic pygame functionality"""
    try:
        pygame.init()
        print("✓ Pygame initialized successfully")
        
        # Try to create a simple display
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Graphics Test")
        print("✓ Display created successfully")
        
        # Fill with color and update
        screen.fill((100, 150, 200))
        pygame.display.flip()
        print("✓ Display updated successfully")
        
        # Keep window open for a moment
        clock = pygame.time.Clock()
        for i in range(60):  # Show for 1 second at 60 FPS
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    break
            clock.tick(60)
        
        pygame.quit()
        print("✓ Basic pygame test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Pygame test failed: {e}")
        return False

def test_opengl():
    """Test OpenGL with pygame"""
    try:
        import pygame
        from pygame.locals import DOUBLEBUF, OPENGL, QUIT
        from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
        from OpenGL.GLU import gluPerspective
        
        pygame.init()
        
        # Try to create OpenGL context
        screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
        print("✓ OpenGL context created successfully")
        
        # Basic OpenGL setup
        glClearColor(0.2, 0.3, 0.8, 1.0)
        gluPerspective(45, (800.0/600.0), 0.1, 50.0)
        
        # Render a few frames
        for i in range(30):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            pygame.display.flip()
            pygame.time.wait(16)  # ~60 FPS
        
        pygame.quit()
        print("✓ OpenGL test passed!")
        return True
        
    except Exception as e:
        print(f"✗ OpenGL test failed: {e}")
        return False

def main():
    print("Graphics System Test")
    print("=" * 20)
    
    # Test basic pygame
    pygame_works = test_pygame()
    
    if pygame_works:
        print("\nTesting OpenGL...")
        opengl_works = test_opengl()
        
        if opengl_works:
            print("\n🎉 All graphics tests passed!")
            print("You can run the 3D simulation!")
        else:
            print("\n⚠️  OpenGL failed, but basic graphics work.")
            print("Try running with software OpenGL:")
            print("LIBGL_ALWAYS_SOFTWARE=1 python main_opengl.py")
    else:
        print("\n❌ Basic graphics failed.")
        print("Check your display and graphics drivers.")

if __name__ == "__main__":
    main()
