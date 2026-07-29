import { TestBed, ComponentFixture } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ModelInventoryComponent } from './model-inventory.component';
import { APIService } from '../../services/api.service';
import { of } from 'rxjs';

describe('ModelInventoryComponent', () => {
  let component: ModelInventoryComponent;
  let fixture: ComponentFixture<ModelInventoryComponent>;
  let apiService: jasmine.SpyObj<APIService>;

  beforeEach(async () => {
    const apiServiceSpy = jasmine.createSpyObj('APIService', ['getModels']);

    await TestBed.configureTestingModule({
      declarations: [ModelInventoryComponent],
      imports: [HttpClientTestingModule],
      providers: [
        { provide: APIService, useValue: apiServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ModelInventoryComponent);
    component = fixture.componentInstance;
    apiService = TestBed.inject(APIService) as jasmine.SpyObj<APIService>;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load models on init', () => {
    const mockModels = [
      {
        id: 1,
        name: 'test-model',
        owner: 'team',
        framework: 'sklearn',
        algorithm: 'rf',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        versions: []
      }
    ];
    apiService.getModels.and.returnValue(of(mockModels));

    component.ngOnInit();

    expect(component.models.length).toBe(1);
    expect(apiService.getModels).toHaveBeenCalled();
  });
});
